#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive
apt_opts=(
  -o Acquire::Retries=5
  -o Acquire::http::Timeout=45
  -o Acquire::https::Timeout=45
)

echo '==> Updating apt indexes (bounded, with retries)'
timeout 15m sudo apt-get "${apt_opts[@]}" update

echo '==> Installing media system packages (bounded, with retries)'
timeout 20m sudo apt-get "${apt_opts[@]}" install -y --no-install-recommends \
  ffmpeg libass-dev libraqm0 fonts-hosny-amiri

echo '==> Installing Python dependencies (bounded, with retries)'
timeout 20m python -m pip install \
  --disable-pip-version-check \
  --retries 5 \
  --timeout 45 \
  --prefer-binary \
  --upgrade \
  -r requirements.txt

echo '==> Verifying runtime imports and FFmpeg'
ffmpeg -version | sed -n '1p'
python - <<'PY'
import gradio_client
import imageio_ffmpeg
import numpy
import requests
from PIL import Image

print('Python imports: OK')
print('ImageIO FFmpeg binary:', imageio_ffmpeg.get_ffmpeg_exe())
PY
