#!/usr/bin/env bash
# One-time setup for tools/uat (skill aa-uat-video): Playwright (pinned in package.json) + Chromium, two Python venvs
# (venv: Kokoro English; venv-vi: VieNeu Vietnamese) and the Kokoro model files. All free, local, no API key.
# VieNeu downloads its own weights into models/hf on first use. venv/, venv-vi/, models/, node_modules/ are gitignored.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
npm install --no-audit --no-fund
npx playwright install chromium
[ -x venv/bin/python ] || python3 -m venv venv
./venv/bin/pip install -q -r requirements.txt
[ -x venv-vi/bin/python ] || python3 -m venv venv-vi
./venv-vi/bin/pip install -q -r requirements-vi.txt
mkdir -p models
K=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s models/kokoro-v1.0.int8.onnx ] || curl -fL -o models/kokoro-v1.0.int8.onnx "$K/kokoro-v1.0.int8.onnx"
[ -s models/voices-v1.0.bin ] || curl -fL -o models/voices-v1.0.bin "$K/voices-v1.0.bin"
command -v ffmpeg >/dev/null || echo "WARN: ffmpeg missing (sudo apt install ffmpeg fonts-dejavu-core)"
echo "tools/uat ready"
