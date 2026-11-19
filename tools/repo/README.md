# Repo tools (AA-1161)

Keep every repo lean: git keeps every committed blob for ever, and shrinking a public repo afterwards needs a history
rewrite and a force push. Rule (tech lead decision S285): a change commits at most about 5-10 key screenshots,
compressed (at most 500 KiB each, about 5-10 MiB per change); full screenshot sets and videos go to the Google Drive
AdventureAsia folder or the private S3 audit-assets prefix, linked from the page. Build artifacts (Lambda zips,
`dist/`), binaries and large data dumps never go into git: CI or Terraform builds them, S3 / ECR / workflow artifacts
store them.

| File | What it does |
|---|---|
| `lean_guard.py` | Refuses, among the files a change adds or changes (`--base <ref> [--head <ref>]`, three-dot diff): a raster image over 500 KiB (`image-size`), more than 10 MiB of images (`image-total`), a `*.zip` under a `dist/` folder (`dist-zip`), an ELF / Mach-O / PE executable whatever its name (`executable`), any file over 5 MiB (`file-size`). A path listed in the repo's `.lean-allow` with a reason (`<path or glob> <reason>`) is exempt. A pure rename and a deletion are never checked. Exit 0 clean, 1 refused, 2 usage / git / `.lean-allow` error. Stdlib only. |
| `test_lean_guard.py` | Its unit tests (throwaway git repos; a 600 KiB image and `dist/x.zip` refused, a compressed screenshot accepted). |

The compressor the guard suggests is [`tools/docs/compress_images.py`](../docs/compress_images.py) (root only; needs
Pillow, e.g. `apps/AA-CIS-App/.venv/bin/python tools/docs/compress_images.py <files or folder>`).

## Where it runs

| Repo | Push time | Pull request |
|---|---|---|
| AA-Ecosys (root) | `scripts/pre-push.sh`, checks `lean-guard` (every push) and `lean-unit` (when `tools/repo/` changes) | `.github/workflows/lean-guard.yml` |
| AA-CIS-App, AA-Booking, AA-Partner, AA-TripPlanner-Web, AA-CIS-Infra | `scripts/pre-push.sh`, check `lean-guard` / `lean_guard` (every push) | `.github/workflows/change-guard.yml`, job `lean` (pull_request and merge_group) |

The CI job is blocking (a red check); making it a required check is a branch-protection change for the tech lead.

## Copies in the five child repos

`lean_guard.py` and `test_lean_guard.py` are vendored byte-identical into `tools/repo/` of AA-CIS-App, AA-Booking,
AA-Partner, AA-TripPlanner-Web and AA-CIS-Infra (each repo's hook and CI run their own copy). Change the limits or a
rule here first, then copy both files to the five repos in the same wave, and check from the workspace root:

```bash
for f in lean_guard.py test_lean_guard.py; do for r in apps/AA-CIS-App apps/AA-Booking apps/AA-Partner apps/AA-TripPlanner-Web infra/AA-CIS-Infra; do cmp tools/repo/$f $r/tools/repo/$f; done; done
```

## Run locally

```bash
python3 -B -m unittest discover -s tools/repo -p 'test_*.py'
python3 tools/repo/lean_guard.py --base origin/master          # child repos: --base origin/main
```

The limits are the tech lead's repo policy, the same in every repo, kept as constants at the top of `lean_guard.py`
(a git hook has no admin settings page; a per-repo override would let one repo drift). History already in git is
not touched by the guard: shrinking it is AA-1161 phase 2, a separate decision.
