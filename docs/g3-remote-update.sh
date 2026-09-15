#!/usr/bin/env bash
# G3 — cập nhật git remote sang org mới AdventureAsia365-Ecosys.
# CHẠY SAU KHI đã đổi tên org trên GitHub (Task 8). GitHub tự redirect remote cũ,
# nhưng cập nhật URL cho tường minh, tránh lệ thuộc redirect lâu dài.
#
# Cách dùng:  bash docs/g3-remote-update.sh
# An toàn: chỉ đổi URL remote 'origin', không đụng history/branch.
set -euo pipefail

OLD="AdventureAsia365-CIS"
NEW="AdventureAsia365-Ecosys"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

declare -A REPOS=(
  ["apps/AA-CIS-App"]="AA-CIS-App"
  ["apps/AA-TripPlanner-Web"]="AA-TripPlanner-Web"
  ["infra/AA-CIS-Infra"]="AA-CIS-Infra"
)

for path in "${!REPOS[@]}"; do
  repo="${REPOS[$path]}"
  dir="$ROOT/$path"
  cur="$(git -C "$dir" config --get remote.origin.url || echo '')"
  new_url="https://github.com/$NEW/$repo.git"
  echo "== $path =="
  echo "  cũ : $cur"
  if [[ "$cur" == *"$OLD/$repo"* ]]; then
    git -C "$dir" remote set-url origin "$new_url"
    echo "  mới: $(git -C "$dir" config --get remote.origin.url)"
  else
    echo "  (bỏ qua — remote không khớp mẫu org cũ; kiểm tra thủ công)"
  fi
  # Verify kết nối tới remote mới (yêu cầu đã đổi tên org + có quyền)
  echo -n "  ls-remote: "
  git -C "$dir" ls-remote --heads origin >/dev/null 2>&1 && echo "OK" || echo "FAIL (kiểm tra quyền/tên org)"
  echo
done

echo "Xong. Kiểm tra lại: git -C <repo> remote -v"
