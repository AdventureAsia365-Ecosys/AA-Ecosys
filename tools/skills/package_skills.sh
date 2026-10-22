#!/usr/bin/env bash
# Package the AA_Ecosys skills for claude.ai (Settings → Capabilities → Skills → upload): one zip per skill, each
# holding the folder <name>/ with SKILL.md (+ references/, lessons.md, …), plus aa-skills-all.zip with every skill.
# Output: skill/dist/ (gitignored: generated from skill/<name>/, never edited by hand).
#
#   tools/skills/package_skills.sh                 # every skill
#   tools/skills/package_skills.sh aa-ship aa-session
#   tools/skills/package_skills.sh --changed origin/master~5   # only skills changed since that ref
#
# Source of truth stays skill/<name>/ in this repo (skill/README.md, principle 6). After a session that changed a
# skill, run this and upload the listed zips so claude.ai matches the repo.
set -euo pipefail
root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$root/skill"

names=()
if [ "${1:-}" = "--changed" ]; then
  ref="${2:?--changed needs a git ref}"
  while IFS= read -r d; do [ -f "$d/SKILL.md" ] && names+=("$d"); done < <(
    git diff --name-only "$ref" -- . | sed -n 's#^skill/\([^/]*\)/.*#\1#p' | sort -u)
elif [ $# -gt 0 ]; then
  names=("$@")
else
  for d in */; do d="${d%/}"; [ -f "$d/SKILL.md" ] && names+=("$d"); done
fi
[ ${#names[@]} -gt 0 ] || { echo "package_skills: no skill to package"; exit 0; }

mkdir -p dist
for n in "${names[@]}"; do
  [ -f "$n/SKILL.md" ] || { echo "package_skills: $n has no SKILL.md" >&2; exit 1; }
  head -5 "$n/SKILL.md" | grep -q "^name: $n\$" || { echo "package_skills: $n/SKILL.md front matter name is not '$n'" >&2; exit 1; }
  rm -f "dist/$n.zip"
  python3 - "$n" "dist/$n.zip" <<'PY'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not d.startswith((".", "__pycache__")))
        for f in sorted(files):
            if f.startswith(".") or f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            z.write(p, p)
PY
  echo "skill/dist/$n.zip"
done

# Every skill in one archive (for a full re-sync).
rm -f dist/aa-skills-all.zip
python3 - <<'PY'
import os, zipfile
with zipfile.ZipFile("dist/aa-skills-all.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for d in sorted(os.listdir(".")):
        if d == "dist" or not os.path.isfile(os.path.join(d, "SKILL.md")):
            continue
        for base, dirs, files in os.walk(d):
            dirs[:] = sorted(x for x in dirs if not x.startswith((".", "__pycache__")))
            for f in sorted(files):
                if not f.startswith(".") and not f.endswith(".pyc"):
                    z.write(os.path.join(base, f), os.path.join(base, f))
PY
echo "skill/dist/aa-skills-all.zip"
