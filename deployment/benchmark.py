"""Jetson-only baseline, FP16 engine build, and matched-input profiling."""
import argparse
import functools
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/deployment/v1'
os.environ['YOLO_CONFIG_DIR'] = str(OUT / 'ultralytics-config')
os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['MPLBACKEND'] = 'Agg'
os.environ['OMP_NUM_THREADS'] = '4'


def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def setup_runtime():
    import torch
    from ultralytics import settings
    torch.set_num_threads(4)
    assert torch.cuda.is_available(), 'CUDA is required'
    settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'comet': False})


def predict(model, frame):
    return model.predict(frame, device=0, imgsz=640, rect=False, conf=.25,
                         iou=.7, retina_masks=True, half=False, verbose=False)[0]


def smoke():
    import torch
    import cv2
    import tensorrt
    from ultralytics import YOLO
    manifest = json.loads((OUT / 'input-manifest.json').read_text())
    for name, record in manifest.items():
        assert sha(OUT / name) == record['sha256'], name
    (OUT / 'data/data.yaml').write_text(f'path: {OUT / "data"}\ntrain: images/test\nval: images/test\ntest: images/test\nnames:\n  0: volleyball\n')
    model = YOLO(OUT / 'model.pt')
    predictions = []
    for path in sorted((OUT / 'data/images/test').glob('*.png'))[:5]:
        result = predict(model, cv2.imread(str(path)))
        torch.cuda.synchronize()
        assert model.predictor.device.type == 'cuda'
        assert torch.isfinite(result.boxes.data).all()
        predictions.append({'image': path.name, 'boxes': result.boxes.data.cpu().tolist()})
        cv2.imwrite(str(OUT / ('smoke-' + path.stem + '.jpg')), result.plot())
    versions = {p: importlib.metadata.version(p) for p in ['torch', 'torchvision', 'ultralytics', 'numpy', 'opencv-python', 'onnx']}
    write('environment.json', {'packages': versions, 'tensorrt': tensorrt.__version__,
          'python': sys.version, 'gpu': torch.cuda.get_device_name(),
          'compute_capability': torch.cuda.get_device_capability(),
          'power_mode': subprocess.check_output(['/usr/sbin/nvpmodel', '-q'], text=True),
          'jetson_release': Path('/etc/nv_tegra_release').read_text(),
          'model_sha256': sha(OUT / 'model.pt'), 'source_sha256': sha(OUT / 'IMG_9217.MOV'),
          'script_sha256': sha(__file__),
          'compatibility_note': 'Installed CUDA PyTorch warns sm_87 is not explicitly supported; actual custom segmentation inference is checked here.'})
    write('smoke-result.json', {'cuda_verified': True, 'predictions': predictions})


def build():
    import ast
    import torch
    import onnx
    import tensorrt as trt
    from ultralytics import YOLO
    assert (OUT / 'smoke-result.json').exists()
    began = time.perf_counter()
    # The pinned Ultralytics exporter predates torch's changed dynamo default.
    # Select its intended legacy ONNX path explicitly for reproducible export.
    original = torch.onnx.export
    torch.onnx.export = functools.partial(original, dynamo=False)
    try:
        YOLO(OUT / 'model.pt').export(format='onnx', device='cpu', imgsz=640,
            batch=1, dynamic=False, half=False, simplify=False, opset=17, nms=False)
    finally:
        torch.onnx.export = original
    graph = onnx.load(str(OUT / 'model.onnx'))
    onnx.checker.check_model(graph)
    metadata = {}
    for item in graph.metadata_props:
        try:
            metadata[item.key] = ast.literal_eval(item.value)
        except (ValueError, SyntaxError):
            metadata[item.key] = item.value
    logger = trt.Logger(trt.Logger.INFO)
    builder = trt.Builder(logger)
    assert builder.platform_has_fast_fp16
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 2 << 30)
    config.set_flag(trt.BuilderFlag.FP16)
    config.profiling_verbosity = trt.ProfilingVerbosity.DETAILED
    parser = trt.OnnxParser(network, logger)
    assert parser.parse_from_file(str(OUT / 'model.onnx')), [str(parser.get_error(i)) for i in range(parser.num_errors)]
    serialized = builder.build_serialized_network(network, config)
    assert serialized is not None
    header = json.dumps(metadata).encode()
    with (OUT / 'model-fp16.engine').open('wb') as stream:
        stream.write(len(header).to_bytes(4, 'little'))
        stream.write(header)
        stream.write(serialized)
    # Inspect actual engine precision as well as the builder flag.
    with (OUT / 'model-fp16.engine').open('rb') as stream:
        length = int.from_bytes(stream.read(4), 'little')
        engine_metadata = json.loads(stream.read(length))
        serialized = stream.read()
    runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
    engine = runtime.deserialize_cuda_engine(serialized)
    assert engine is not None
    tensors = [{'name': engine.get_tensor_name(i),
                'dtype': str(engine.get_tensor_dtype(engine.get_tensor_name(i))),
                'shape': list(engine.get_tensor_shape(engine.get_tensor_name(i)))}
               for i in range(engine.num_io_tensors)]
    info = engine.create_engine_inspector().get_engine_information(trt.LayerInformationFormat.JSON)
    (OUT / 'engine-inspection.json').write_text(info)
    write('build-result.json', {'engine_sha256': sha(OUT / 'model-fp16.engine'),
          'onnx_sha256': sha(OUT / 'model.onnx'), 'seconds': time.perf_counter()-began,
          'fp16_enabled': True, 'workspace_gib': 2, 'dynamic': False,
          'input_shape': [1, 3, 640, 640], 'tensors': tensors, 'metadata': engine_metadata,
          'note': 'FP16 internal execution permitted; input/output tensors remain FP32. NMS and mask reconstruction remain in the shared Ultralytics postprocessor.'})


def stats(values):
    import numpy as np
    a = np.asarray(values)
    return {'samples': len(values), 'mean_ms': float(a.mean()), 'median_ms': float(np.median(a)),
            'p95_ms': float(np.percentile(a, 95)), 'fps_from_mean': float(1000/a.mean())}


def benchmark(kind):
    import cv2
    import numpy as np
    import torch
    import psutil
    from ultralytics import YOLO
    weights = OUT / ('model.pt' if kind == 'pytorch' else 'model-fp16.engine')
    model = YOLO(weights, task='segment')
    cap = cv2.VideoCapture(str(OUT / 'IMG_9217.MOV'))
    assert cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
    ok, frame = cap.read()
    cap.release()
    assert ok
    assert frame.shape == (1920, 1080, 3), frame.shape
    for _ in range(30):
        predict(model, frame)
    torch.cuda.synchronize()
    tensor = model.predictor.preprocess([frame])
    assert tuple(tensor.shape) == (1, 3, 640, 640)
    torch.cuda.reset_peak_memory_stats()
    rounds = []
    with torch.inference_mode():
        for repeat in range(3):
            device_ms, wall_ms = [], []
            for _ in range(200):
                start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                t = time.perf_counter()
                start.record()
                output = model.predictor.model(tensor)
                end.record()
                end.synchronize()
                wall_ms.append((time.perf_counter()-t)*1000)
                device_ms.append(start.elapsed_time(end))
            rounds.append({'round': repeat+1, 'gpu_execution': stats(device_ms), 'synchronized_host_call': stats(wall_ms)})
    # Same first 900 consecutive frames, no frame skipping or drawing/encoding.
    cap = cv2.VideoCapture(str(OUT / 'IMG_9217.MOV'))
    assert cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
    count = 900
    measurements = {key: [] for key in ['decode', 'predict_call', 'total', 'preprocess', 'inference', 'postprocess']}
    detections = []
    began = time.perf_counter()
    for index in range(count):
        t = time.perf_counter()
        ok, frame = cap.read()
        assert ok, index
        decoded = time.perf_counter()
        result = predict(model, frame)
        boxes = result.boxes.data.cpu().tolist()
        torch.cuda.synchronize()
        finished = time.perf_counter()
        measurements['decode'].append((decoded-t)*1000)
        measurements['predict_call'].append((finished-decoded)*1000)
        measurements['total'].append((finished-t)*1000)
        for key in ['preprocess', 'inference', 'postprocess']:
            measurements[key].append(float(result.speed[key]))
        detections.append({'frame_index': index, 'boxes': boxes})
        if index in [0, 300, 600, 899]:
            cv2.imwrite(str(OUT / f'{kind}-frame-{index:04d}.jpg'), result.plot())
        if (index+1) % 100 == 0:
            write('status.json', {'stage': kind, 'state': 'running', 'video_frames': index+1, 'total': count})
            print(kind, index+1, flush=True)
    elapsed = time.perf_counter()-began
    cap.release()
    report = {'kind': kind, 'checkpoint_sha256': sha(weights), 'input_shape': list(tensor.shape),
              'script_sha256': sha(__file__), 'source_decoded_shape': list(frame.shape), 'orientation_auto': True,
              'torch_tf32_matmul_allowed': torch.backends.cuda.matmul.allow_tf32,
              'torch_tf32_cudnn_allowed': torch.backends.cudnn.allow_tf32,
              'input_dtype': str(tensor.dtype), 'batch': 1, 'warmup_iterations': 30,
              'network_only_rounds': rounds, 'video_frames': count, 'video_frame_range': [0, count-1],
              'video_source_sha256': sha(OUT / 'IMG_9217.MOV'),
              'video_timings': {k: stats(v) for k, v in measurements.items()},
              'loop_wall_seconds_including_four_preview_writes': elapsed,
              'loop_fps_including_four_preview_writes': count/elapsed,
              'process_rss_bytes': psutil.Process().memory_info().rss,
              'torch_peak_allocated_bytes': torch.cuda.max_memory_allocated(),
              'torch_peak_reserved_bytes': torch.cuda.max_memory_reserved(),
              'memory_note': 'Torch allocator statistics exclude direct TensorRT allocations; use process RSS and tegrastats unified RAM alongside these.',
              'scope': 'Unpaced offline batch-1 processing, original 1080x1920 video. Timings exclude drawing, encoding and network streaming except four saved previews in loop wall time. Source/decode/postprocess identical for both backends.'}
    write(f'{kind}-video-predictions.json', detections)
    write(f'{kind}-benchmark.json', report)


def evaluate(kind):
    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO
    from ultralytics.models.yolo.segment.val import SegmentationValidator

    class SquareValidator(SegmentationValidator):
        def build_dataset(self, img_path, mode='val', batch=None):
            dataset = super().build_dataset(img_path, mode, batch)
            # Both backends must validate with the engine's fixed square input.
            dataset.rect = False
            return dataset

    model = YOLO(OUT / ('model.pt' if kind == 'pytorch' else 'model-fp16.engine'), task='segment')
    metrics = model.val(validator=SquareValidator, data=str(OUT / 'data/data.yaml'),
          split='test', device=0, imgsz=640, batch=1, workers=0, rect=False,
          half=False, plots=True, conf=.001, iou=.7, project=str(OUT / 'validation'),
          name=kind, exist_ok=True, verbose=False)
    rows, tp, fp, fn, empty_fp = [], 0, 0, 0, 0
    for path in sorted((OUT / 'data/images/test').glob('*.png')):
        result = predict(model, cv2.imread(str(path)))
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().tolist()
        masks = result.masks.xy if result.masks is not None else []
        row = {'image': path.name, 'boxes': boxes.tolist(), 'confidences': confs,
               'mask_polygons': [p.tolist() for p in masks]}
        label = (OUT / 'data/labels/test' / path.with_suffix('.txt').name).read_text().split()
        matched = False
        if label:
            p = np.array(list(map(float, label[1:]))).reshape(-1, 2)
            h, w = result.orig_shape
            p *= [w, h]
            gt = np.r_[p.min(0), p.max(0)]
            if len(boxes):
                intersection = np.maximum(0, np.minimum(boxes[:, 2:], gt[2:])-np.maximum(boxes[:, :2], gt[:2])).prod(1)
                union = (boxes[:, 2:]-boxes[:, :2]).prod(1)+np.prod(gt[2:]-gt[:2])-intersection
                matched = bool(np.max(intersection/np.maximum(union, 1e-9)) >= .5)
            tp += int(matched)
            fn += int(not matched)
            fp += len(boxes)-int(matched)
        else:
            fp += len(boxes)
            empty_fp += bool(len(boxes))
        row['matched_at_box_iou_0_5'] = matched
        rows.append(row)
    assert len(rows) == 123
    write(f'{kind}-test-predictions.json', rows)
    write(f'{kind}-accuracy.json', {'images': len(rows), 'metrics': {k: float(v) for k, v in metrics.results_dict.items()},
          'confidence': .25, 'box_iou_match': .5, 'tp': tp, 'fp': fp, 'fn': fn,
          'precision': tp/(tp+fp) if tp+fp else 0, 'recall': tp/(tp+fn),
          'negative_frames_with_false_positive': empty_fp, 'input_shape': [1, 3, 640, 640]})


def orchestrate():
    OUT.mkdir(parents=True, exist_ok=True)
    stages = ['smoke', 'build', 'pytorch', 'tensorrt', 'accuracy-pytorch', 'accuracy-tensorrt']
    expected = ['smoke-result.json', 'build-result.json', 'pytorch-benchmark.json', 'tensorrt-benchmark.json', 'pytorch-accuracy.json', 'tensorrt-accuracy.json']
    for stage, result in zip(stages, expected):
        if (OUT / result).exists():
            print('Retaining completed', stage, flush=True)
            continue
        write('status.json', {'stage': stage, 'state': 'running'})
        with (OUT / f'{stage}.log').open('a') as log, (OUT / f'{stage}-tegrastats.log').open('w') as telemetry:
            monitor = subprocess.Popen(['tegrastats', '--interval', '1000'], stdout=telemetry, stderr=subprocess.STDOUT)
            try:
                subprocess.run([sys.executable, __file__, '--stage', stage], stdout=log, stderr=subprocess.STDOUT, check=True)
            finally:
                monitor.terminate()
                monitor.wait(timeout=10)
    write('status.json', {'stage': 'complete', 'state': 'complete'})
    print('COMPLETE baseline, FP16 engine, matched profiling and accuracy checks', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage')
    args = parser.parse_args()
    try:
        if args.stage:
            setup_runtime()
            if args.stage == 'smoke': smoke()
            elif args.stage == 'build': build()
            elif args.stage.startswith('accuracy-'): evaluate(args.stage.removeprefix('accuracy-'))
            else: benchmark(args.stage)
        else:
            orchestrate()
    except Exception as error:
        write('status.json', {'stage': args.stage or 'orchestration', 'state': 'failed', 'error': str(error)})
        raise
