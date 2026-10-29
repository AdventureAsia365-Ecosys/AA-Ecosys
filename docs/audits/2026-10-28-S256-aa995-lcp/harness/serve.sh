#!/usr/bin/env bash
# AA-995 S256: (re)start `next start` on :3995 for the worktree build, against the mock browse server on :3996.
# Usage: bash serve.sh <log-label>
D=/home/nghiep/projects/AA-Ecosys/.tmp-session/S256/aa995
W=/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/tp-aa995-lcp/frontend
PID=$(ss -ltnp 2>/dev/null | grep ':3995 ' | sed -E 's/.*pid=([0-9]+).*/\1/')
[ -n "$PID" ] && kill "$PID" && sleep 2
cd $W && BROWSE_API_URL=http://127.0.0.1:3996 TRIP_API_URL=http://127.0.0.1:3996 nohup npx next start -p 3995 > $D/start-$1.log 2>&1 &
sleep 7
for u in / /destinations /destinations/bhutan /tours/sri-lanka-cultural-tour-kandy-dambulla-and-sigiriya-3-days-sri-lanka-28e22489; do
  curl -s -o /dev/null -w "$u %{http_code}\n" http://localhost:3995$u
done
