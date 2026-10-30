#!/usr/bin/env bash
# UAT video pipeline (skill aa-uat-video): captions -> local TTS -> record (each step held to its narration)
# -> subtitles + EN/VI audio mux -> sync check. $0: local TTS + local ffmpeg, no API call.
#   bash tools/uat/run.sh scenarios/<app>/<id>.cjs        (path relative to tools/uat/, or absolute)
# Setup once: bash tools/uat/setup.sh. Exit: 0 PASS | 2 a step FAILed (video kept) | 3 egress not VN (VPN on).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
SC="$(realpath "${1:?scenario path, e.g. scenarios/tripplanner/tp-pub-01.cjs}")"
[ -d node_modules/@playwright/test ] || { echo "STOP: run bash tools/uat/setup.sh first"; exit 1; }
c=$(curl -s --max-time 10 https://ipinfo.io/country || true)
[ "$c" = "VN" ] || { echo "STOP: public IP country is '$c', not VN (Vercel blocks VPN IPs). Turn the VPN off."; exit 3; }
ID="$(node -e "console.log(require(process.argv[1]).id)" "$SC")"
node record.cjs "$SC" --captions
./venv/bin/python -I tts.py "work/$ID"
set +e; node record.cjs "$SC"; rc=$?; set -e
MP4="$(./venv/bin/python -I build.py "work/$ID" out | tail -1)"
if ! ./venv/bin/python -I check_sync.py "$MP4" "${MP4%.mp4}.en.srt" --frames "work/$ID/frames"; then
  rc=$(( rc == 0 ? 2 : rc ))
fi
echo "video $MP4 (verdict in ${MP4%.mp4}.result.json); look at work/$ID/frames/*.png"
exit $rc
