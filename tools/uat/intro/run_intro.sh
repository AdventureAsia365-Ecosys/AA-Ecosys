#!/usr/bin/env bash
# TripPlanner product intro video (skill aa-uat-video): one command per language.
#   bash tools/uat/intro/run_intro.sh en|vi      (setup once: bash tools/uat/setup.sh)
# narration clips (local TTS) -> record the live site, each scene held to its narration -> MP4 with that
# language's narration + burned-in subtitles (+ .srt/.vtt) in out/intro/. $0: public pages, local TTS/ffmpeg.
# Run one language at a time (one Chromium; VieNeu needs ~1.9 GB RAM). Needs `curl ipinfo.io/country` = VN.
set -euo pipefail
LANG_ID="${1:?en|vi}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
[ -d node_modules/@playwright/test ] || { echo "STOP: run bash tools/uat/setup.sh first"; exit 1; }
c=$(curl -s --max-time 10 https://ipinfo.io/country || true)
[ "$c" = "VN" ] || { echo "STOP: public IP country is '$c', not VN (Vercel blocks the VPN). Turn the VPN off."; exit 3; }
./venv/bin/python -I intro/tts_intro.py "$LANG_ID"
node intro/record_intro.cjs "$LANG_ID"
./venv/bin/python -I intro/build_intro.py "$LANG_ID"
python3 -I intro/gen_docs.py
