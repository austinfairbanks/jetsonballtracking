# Roadmap

The goal is a pan/tilt camera that follows the volleyball during play. Detection
runs on the Jetson today. The remaining work is to track the ball between
frames and control the camera's motors using its position in the image.

## Done — perception proof of concept

Recorded eight source videos and annotated 644 keyframes, mostly with SAM 2.1
Large assistance in CVAT. After excluding two duplicates, recording-grouped
three-fold CV used 519 development images; 123 images remained held out. The
final YOLO11n-seg model was evaluated on those images and run independently on
all 5,528 frames of the selected backyard video.

The custom checkpoint runs on the Jetson Orin Nano. ONNX export and a native
TensorRT FP16 build reduced mean model-call latency from 24.72 to 4.92 ms.
Both versions were timed on the same 900 video frames and evaluated on the same
123 test images. The live camera application processes about 15 FPS and shows
boxes, masks and box-center markers in a browser.

The [recorded demo](docs/media/jetson-demo.mp4) now shows backyard predictions,
the hardware and live room detections. The moving-camera system and the
performance targets below still need to be tested.

[Dataset preparation](DATASET_PREPARATION.md) ·
[Training results](TRAINING_RESULTS.md) ·
[Deployment measurements](DEPLOYMENT_RESULTS.md)

## Now — reduce false detections and improve live FPS

Collect Jetson-camera footage with and without the ball, including ordinary
backyard lighting and motion. Prioritize scenes where the model detects other
objects as volleyballs. Use development data to
select the confidence threshold, then freeze it before evaluating fresh,
separately recorded test sessions. Recompute localization using both the box
IoU and ground-truth mask-coverage rules.

Profile capture, preprocessing, inference and postprocessing separately. Isolate
why camera capture delivers about 15 FPS, then remeasure on ball-present
and empty scenes after warmup. Model-call speed alone does not establish live
throughput or capture-to-display latency.

**Check:** precision, recall, false detections on images without the ball,
processed FPS and processing p95. Targets remain **30 FPS**,
**p95 ≤33 ms** from decoded frame to prediction, and **>99% precision** with as
much recall as possible. See [the exact criteria](LIVE_REQUIREMENTS.md).

## Next — track the ball between frames

Compare ball positions and timestamps from consecutive frames to estimate
direction and speed in image coordinates. Use those estimates to predict
position during short missed detections. Test what happens when the ball leaves
the frame, returns, bounces or changes direction before choosing a tracker.

**Check:** show detected and predicted positions separately on replayed video.
Measure prediction error on labeled frames and how long it takes to find the
ball again after losing it. Include examples where tracking fails.

## Then — add pan and tilt control

Choose the mount, motors and motor interface. Measure how camera rotation
changes an object's position in the image. Use the ball's offset from the image
center to command pan and tilt, then check the next image to see whether that
movement brought the ball closer to the center. The tracker must account for
the camera turning when estimating ball movement.

**Check:** demonstrate the moving camera following the ball. Measure distance
from the image center, overshoot, response delay and recovery after losing it.
Controller choice, motor hardware and numeric control targets are still open.

## Later — test more playing conditions

Validate the full system during setting, serving, rolling and holding in the
backyard, across normal playing light. Expand toward indoor and outdoor use
with this specific ball. Use observed failures to decide whether more data,
a different model or changes to capture/control are worth the complexity.

Record the distances, ball sizes, speeds, visibility and lighting actually
tested, including conditions where the system stops working reliably.
