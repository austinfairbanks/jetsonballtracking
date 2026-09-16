#!/bin/bash
# Run natively on the Mac, outside the sandbox, to install the Apple GPU worker.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local
if [ ! -x .local/sam2-venv/bin/python ]; then
    uv venv --python 3.12 .local/sam2-venv
fi
uv pip install --python .local/sam2-venv/bin/python -r sam2/requirements.txt
SAM2_BUILD_CUDA=0 uv pip install --no-build-isolation --python .local/sam2-venv/bin/python \
    'SAM-2 @ https://github.com/facebookresearch/sam2/archive/2b90b9f5ceec907a1c18123530e92e794ad901a4.zip'
if [ ! -f .local/sam2.1_hiera_large.pt ]; then
    curl --fail --location --retry 3 \
        https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt \
        -o .local/sam2.1_hiera_large.pt.download
    mv .local/sam2.1_hiera_large.pt.download .local/sam2.1_hiera_large.pt
fi
shasum -a 256 -c <<'CHECKSUM'
2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318  .local/sam2.1_hiera_large.pt
CHECKSUM
.local/sam2-venv/bin/python -c 'import torch; assert torch.backends.mps.is_available(), "Apple GPU unavailable"'
.local/sam2-venv/bin/python sam2/install_service.py
