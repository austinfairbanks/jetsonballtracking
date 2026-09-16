#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv_bin="$HOME/.local/bin/uv"
"$uv_bin" venv --python /usr/bin/python3 --allow-existing .venv-deploy
# Reuse verified CUDA wheels without modifying the working detector environment.
printf '%s\n' "$PWD/.venv-detect/lib/python3.12/site-packages" /usr/lib/python3.12/dist-packages > .venv-deploy/lib/python3.12/site-packages/jetson-runtime.pth
"$uv_bin" pip install --python .venv-deploy/bin/python --no-deps ultralytics==8.3.204 onnx==1.17.0 protobuf==5.29.5
.venv-deploy/bin/python -c 'import torch, torchvision, tensorrt, ultralytics, onnx; print(torch.__version__, torchvision.__version__, tensorrt.__version__, ultralytics.__version__, onnx.__version__); assert torch.cuda.is_available()'
