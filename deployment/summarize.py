"""Summarize measured Jetson results; run after copying reports to the Mac."""
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/deployment/v1'


def load(name):
    return json.loads((OUT / name).read_text())


def telemetry(kind):
    text = (OUT / f'{kind}-tegrastats.log').read_text()
    ram = [float(v) for v in re.findall(r'RAM (\d+)/', text)]
    temps = [float(v) for v in re.findall(r'gpu@([\d.]+)C', text)]
    power = [float(v)/1000 for v in re.findall(r'VDD_IN (\d+)mW', text)]
    return {'system_ram_peak_mib': max(ram) if ram else None,
            'gpu_temperature_peak_c': max(temps) if temps else None,
            'board_input_power_mean_w': statistics.mean(power) if power else None,
            'board_input_power_peak_w': max(power) if power else None,
            'samples': len(ram)}


def main():
    a, b = load('pytorch-benchmark.json'), load('tensorrt-benchmark.json')
    qa, qb = load('pytorch-accuracy.json'), load('tensorrt-accuracy.json')
    def network(report, field):
        return statistics.mean(r[field]['mean_ms'] for r in report['network_only_rounds'])
    aw, bw = network(a, 'synchronized_host_call'), network(b, 'synchronized_host_call')
    ag, bg = network(a, 'gpu_execution'), network(b, 'gpu_execution')
    ta, tb = telemetry('pytorch'), telemetry('tensorrt')
    deltas = {k: qb['metrics'][k]-v for k, v in qa['metrics'].items() if k.startswith('metrics/')}
    summary = {'network_host_speedup': aw/bw, 'network_gpu_span_speedup': ag/bg,
               'offline_processing_speedup': a['video_timings']['total']['mean_ms']/b['video_timings']['total']['mean_ms'],
               'accuracy_delta_tensorrt_minus_pytorch': deltas,
               'telemetry': {'pytorch': ta, 'tensorrt': tb},
               'mask_map50_95_drop_under_half_percentage_point': deltas['metrics/mAP50-95(M)'] >= -.005,
               'box_map50_95_drop_under_half_percentage_point': deltas['metrics/mAP50-95(B)'] >= -.005}
    (OUT / 'comparison.json').write_text(json.dumps(summary, indent=2)+'\n')
    def row(label, x, y, unit=''):
        return f'| {label} | {x:.2f}{unit} | {y:.2f}{unit} |'
    lines = ['# Jetson YOLO11n-seg deployment results', '',
             'Measured on Jetson Orin Nano in its existing 25 W mode, with default dynamic',
             'clocks, JetPack 7.2.1 and TensorRT 10.16.2.10. Both backends use the same',
             'checkpoint, batch 1, 640×640 input, confidence 0.25 and NMS IoU 0.7.', '',
             'PyTorch uses FP32 weights/inputs with its default cuDNN TF32 permission enabled;',
             'matmul TF32 permission is disabled. The exact flags are saved with each profile.', '',
             '| Measurement | PyTorch CUDA FP32 | TensorRT FP16 |', '| --- | ---: | ---: |',
             row('Model call FPS, synchronized host timing', 1000/aw, 1000/bw),
             row('Mean model call latency', aw, bw, ' ms'),
             row('Mean CUDA-event model span', ag, bg, ' ms'),
             row('Offline decode + prediction FPS', a['video_timings']['total']['fps_from_mean'], b['video_timings']['total']['fps_from_mean']),
             row('Offline processing p95 latency', a['video_timings']['total']['p95_ms'], b['video_timings']['total']['p95_ms'], ' ms'),
             row('Process RSS at end of profile', a['process_rss_bytes']/2**20, b['process_rss_bytes']/2**20, ' MiB'),
             row('System RAM peak during profile', ta['system_ram_peak_mib'], tb['system_ram_peak_mib'], ' MiB'),
             row('GPU temperature peak during profile', ta['gpu_temperature_peak_c'], tb['gpu_temperature_peak_c'], ' °C'),
             row('Mean board input power during profile', ta['board_input_power_mean_w'], tb['board_input_power_mean_w'], ' W'), '',
             f'**Model-call speedup: {aw/bw:.2f}×. Offline processing speedup: {summary["offline_processing_speedup"]:.2f}×.**', '',
             'Model-call results average three rounds of 200 calls after 30 warmups, on',
             'one preprocessed GPU-resident image. CUDA-event spans can include launch gaps;',
             'host timing includes Python dispatch and synchronization. These are not camera FPS.', '',
             'Offline results use the same 900 consecutive source frames (0–899) from',
             'IMG_9217.MOV, including decoding, resize/transfer, inference, NMS and full-resolution',
             'mask reconstruction. They exclude annotation, encoding and network streaming.',
             'System memory/power/temperature samples cover both benchmark phases and are',
              'whole-device measurements, not model-exclusive GPU allocation.', '',
              'The source is HEVC decoded through OpenCV/FFmpeg with no hardware acceleration',
              'requested/reported. Decoder time is a substantial part of the offline pipeline.', '',
             '## Prediction quality after conversion', '',
             '| Metric on 123 labeled test images | PyTorch | TensorRT |', '| --- | ---: | ---: |']
    for name in ['metrics/mAP50(B)', 'metrics/mAP50-95(B)', 'metrics/mAP50(M)', 'metrics/mAP50-95(M)']:
        lines.append(row(name.removeprefix('metrics/'), qa['metrics'][name]*100, qb['metrics'][name]*100, '%'))
    lines += [row('Fixed-threshold precision', qa['precision']*100, qb['precision']*100, '%'),
              row('Fixed-threshold recall', qa['recall']*100, qb['recall']*100, '%'),
              f"| TP / FP / FN | {qa['tp']} / {qa['fp']} / {qa['fn']} | {qb['tp']} / {qb['fp']} / {qb['fn']} |", '',
              'Both evaluations force identical square inputs. Earlier Mac results used',
              'different padding/batching, so this matched Jetson baseline is the appropriate',
              'reference for conversion changes. No model or threshold was tuned on these results.', '',
              'The two additional FP16 false detections occur in images 605 and 641, with',
              'confidence approximately 0.2517 and 0.2510, just above the fixed 0.25 threshold.', '',
              '## Deployment and scope', '',
              'The engine has static input shape 1×3×640×640. Internal FP16 execution is enabled;',
              'input/output tensors remain FP32 and NMS/mask reconstruction use the shared',
              'Ultralytics postprocessor. The engine is specific to this target/runtime.', '',
              'The installed CUDA PyTorch wheel warns that Orin sm_87 is not explicitly supported.',
              'Real custom segmentation and profiling completed on CUDA; the warning remains an',
              'environment maintenance limitation, not evidence of a YOLO architecture failure.', '',
              'The profile establishes feasibility on this board at this input size. It does',
              'not establish performance on new camera environments, long-duration thermal',
              'stability, or fast/small-ball accuracy. Camera capture and streaming can impose',
              'separate throughput limits.', '',
              '[Protocol and commands](deployment/README.md) ·',
              '[Raw comparison](artifacts/deployment/v1/comparison.json) ·',
              '[Engine](artifacts/deployment/v1/model-fp16.engine)', '']
    live = OUT / 'live-test-report.json'
    if live.exists():
        report = load('live-test-report.json')
        lines += ['## Live camera check', '',
                  f"Processed {report['frames']} frames in {report['wall_seconds']:.2f} seconds "
                  f"({report['processed_fps']:.2f} FPS), status: {report['status']}.", '',
                  'This includes camera waits, inference, drawing, JPEG creation and preview writes.',
                  'The inspected live image was nearly black; this verifies processing stability,',
                  'not live volleyball recognition in the room. A visible-ball camera check remains future work.',
                  'It is not capture-to-display latency. The browser stream itself is capped at 10 FPS.', '',
                  'Viewer: run `bash deployment/live.sh status` for the private URL.', '']
    (ROOT / 'DEPLOYMENT_RESULTS.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
