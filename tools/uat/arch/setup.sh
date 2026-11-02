#!/usr/bin/env bash
# Architecture video tools (AA-1021): one-time local setup, no root, $0.
#   bash tools/uat/arch/setup.sh            (cache: tools/uat/arch/.cache, gitignored; override with ARCH_VIDEO_CACHE)
# - IBM Plex Sans (SIL OFL 1.1) from the google/fonts repo at a pinned commit, sha256-checked: the theme and caption font.
# - tesseract 5 + English data for gate layer 3 (OCR), unpacked from the Ubuntu archive with apt-get download +
#   dpkg -x (signed archive, no sudo); gate.py finds it in <cache>/ocr/root.
# - the official AWS Architecture Icons (the published asset package, pinned URL + sha256; AWS permits their use in
#   architecture diagrams): sketch.py extracts the icons it draws into <cache>/aws-icons and drops the zip.
# The narration needs tools/uat/setup.sh first (venv with kokoro-onnx, models/, Playwright in node_modules).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CACHE=${ARCH_VIDEO_CACHE:-$HERE/.cache}
FONT_COMMIT=0b58fb370093f9a9f4ff785d94405710b79de67c
FONT_SHA256=3b031aa4216174205bd8471f88a49b91f093169e9e87bd5262242bc5967fe2e3
ICONS_URL=https://d1.awsstatic.com/onedam/marketing-channels/website/public/shared/architecture-icon-release/Icon-package_07312026.5846e92413caa21490223536cc97f1269e44fa92.zip
ICONS_SHA256=d2d166c453526471749d520e0db022c459abef759d2946cf2dd1d1c992dc6526
mkdir -p "$CACHE/fonts" "$CACHE/ocr"

if [ ! -f "$CACHE/fonts/IBMPlexSans-VF.ttf" ]; then
  base="https://raw.githubusercontent.com/google/fonts/$FONT_COMMIT/ofl/ibmplexsans"
  curl -sSfL -o "$CACHE/fonts/IBMPlexSans-VF.ttf.part" "$base/IBMPlexSans%5Bwdth,wght%5D.ttf"
  echo "$FONT_SHA256  $CACHE/fonts/IBMPlexSans-VF.ttf.part" | sha256sum -c --quiet
  mv "$CACHE/fonts/IBMPlexSans-VF.ttf.part" "$CACHE/fonts/IBMPlexSans-VF.ttf"
  curl -sSfL -o "$CACHE/fonts/OFL.txt" "$base/OFL.txt"
fi
echo "font: $CACHE/fonts/IBMPlexSans-VF.ttf"

if command -v tesseract >/dev/null 2>&1; then
  echo "ocr: $(tesseract --version 2>&1 | head -1) on PATH"
elif [ ! -x "$CACHE/ocr/root/usr/bin/tesseract" ]; then
  mkdir -p "$CACHE/ocr/debs" "$CACHE/ocr/root"
  (cd "$CACHE/ocr/debs" && apt-get download tesseract-ocr tesseract-ocr-eng libtesseract5 liblept5 libarchive13t64 libgif7)
  for d in "$CACHE"/ocr/debs/*.deb; do dpkg -x "$d" "$CACHE/ocr/root"; done
fi
if [ -x "$CACHE/ocr/root/usr/bin/tesseract" ]; then
  LD_LIBRARY_PATH="$CACHE/ocr/root/usr/lib/x86_64-linux-gnu" "$CACHE/ocr/root/usr/bin/tesseract" --version 2>&1 | head -1
fi

if ! grep -qs "Icon-package_07312026" "$CACHE/aws-icons/VERSION"; then
  rm -rf "$CACHE/aws-icons" && mkdir -p "$CACHE/aws-icons"
  curl -sSfL -o "$CACHE/aws-icons.zip.part" "$ICONS_URL"
  echo "$ICONS_SHA256  $CACHE/aws-icons.zip.part" | sha256sum -c --quiet
  python3 -I "$HERE/sketch.py" --extract-icons "$CACHE/aws-icons.zip.part" "$CACHE/aws-icons"
  rm -f "$CACHE/aws-icons.zip.part"
fi
echo "icons: $(cat "$CACHE/aws-icons/VERSION") in $CACHE/aws-icons"
