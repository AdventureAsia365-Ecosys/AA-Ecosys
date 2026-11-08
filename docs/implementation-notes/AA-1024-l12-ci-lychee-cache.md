# AA-1024: the lychee binary from a cached, hash-checked copy (lane l12-ci-lychee-cache, S273)

On 08/11 the Docs lint step "Internal links (offline)" failed several times, and each time the only cause was the
binary download. lycheeverse/lychee-action v2.9.0 downloads the lychee v0.24.2 tarball from github.com on every run,
with one bare `curl -sfLO` and no retry (curl exit 22 after about 2 minutes). Each failure also took pull requests out
of the merge queues (root #633, Partner #249). The same change goes into five repos with identical files: the root
repo, AA-Booking, AA-Partner, AA-TripPlanner-Web and AA-CIS-Infra. AA-CIS-App has no lychee step and has no change.

## Decisions

- **The action is replaced, not kept.** lychee-action v2.9.0 has no input that skips its download. Its `lycheeVersion`
  input only picks which version to download. A local composite action, `.github/actions/lychee`, does what it did.
  `.github/scripts/lychee_bin.py run` copies the action's `entrypoint.sh`. The command is the same:
  `lychee --mode task --format markdown --output <tmp> <args>`. The report goes to `lychee/out.md`, to the log and,
  with `jobSummary`, to the step summary. `exit_code` is written to `$GITHUB_OUTPUT`. A report that finds 0 links fails
  (`failIfEmpty`). lychee's exit code is passed on (`fail`). The arguments are split the way a shell splits them, so
  quoted globs reach lychee unchanged, as they did with the action's `eval`.
- **The pin is in the repo.** `.github/actions/lychee/pins.txt` holds one line per runner platform (x86_64 and
  aarch64): version, target and the sha256 of the tarball. Each sha256 comes from the release's own
  `<asset>.sha256` file, and the GitHub asset digest gives the same value. The x86_64 tarball was downloaded and
  checked against it. `lychee_bin.py` refuses a pin file that pins two versions, pins one target twice or has a
  malformed line.
- **Cache key.** The key is `lychee-v1-<version>-<target>-<sha256>`, on the path `${{ runner.temp }}/lychee-cache`. The
  tarball is cached, and its sha256 is checked on every run, a cache hit included. Only the `lychee` member is
  extracted, and only from the archive's top level or one folder down. A symlink or a deeper path is not used.
- **The download runs only on a miss.** It goes through urllib, which speaks HTTP/1.1. It makes 6 attempts, with
  backoff of 5/10/20/40/60 s plus jitter. Bytes that do not match the pin are deleted, and the pin is never relaxed.
  This is the same shape as `url_wheels.py` in AA-CIS-App (#1388).
- **Restore and save are explicit** (`actions/cache/restore` and `actions/cache/save`, pinned by SHA to v6.1.0, the
  same SHA as CIS `url-wheels`). The save runs right after the verified download. With the plain `actions/cache`, the
  save waits for the post step, which is skipped when any later Docs lint check fails.
- **A warm job runs on the default branch.** GitHub lets every pull request and merge-queue run read a cache entry
  saved on the default branch. A pull-request ref cannot read another pull request's entry. The Docs lint job runs on
  pull requests (and on `merge_group` in Booking and Partner), so a new job, `lychee-cache` ("Lychee cache (default
  branch)"), runs on these events: a push to main/master that changes the action or the script, the weekly schedule,
  and a manual run. It only restores or downloads the binary, then saves it. The `lint` job now skips `push` as well as
  `schedule`. Its name "Docs lint" is unchanged, because it is a required check and a merge-queue check.
- **The pull-request path filters** of the root and Infra Docs lint now include `.github/actions/lychee/**` and
  `.github/scripts/lychee_bin.py`, so a change to either runs the link check. Booking, Partner and TripPlanner have no
  path filter.

## Changed

- `.github/actions/lychee/{action.yml,pins.txt}`, `.github/scripts/lychee_bin.py`, `.github/scripts/test_lychee_bin.py`
  are new. These four files are byte-identical in all five repos.
- `docs-lint.yml`: the "Internal links (offline)" step uses `./.github/actions/lychee` with the same `args`, `fail` and
  `jobSummary` as before. The workflow also has a push trigger (paths: the action and the script) and the warm job.
- `workflow-lint.yml` runs `test_lychee_bin.py` and lists the two script files in its path filters.
- `scripts/pre-push.sh`: the hint for a missing lychee no longer names lychee-action. It says how to fetch the same
  verified binary with `lychee_bin.py fetch`. Only the hint text changed.
- `tools/docs/README.md`: one paragraph on the pinned binary and the local fetch command.

## Tradeoffs

- The action's `GITHUB_TOKEN` export is dropped. Every lychee config here has `offline = true`, so lychee never makes
  an HTTP request and never needs a token.
- The first pull request after a pin change still downloads the binary, if it runs before the push warm job on
  main/master has finished. It now has 6 attempts instead of 1. A cache entry is evicted after 7 days with no access.
  Pull requests read the entry and so keep it alive, and the weekly schedule saves it again.
- Workflow Lint still downloads actionlint from github.com (`curl --retry 3`). It is not a required check, so it stays
  as it is. A follow-up could move it to the same cached shape.

## Should know

- To move the lychee version, change every line of `pins.txt` in all five repos in one wave. Take each sha256 from the
  release's `.sha256` files, then check it against the downloaded tarball.
- The tests are offline: the network is faked and the archives are synthetic. In each repo, a test reads the committed
  `docs-lint.yml` and checks the job name "Docs lint", the step name, the local action, the warm job and the trigger
  paths. It also checks that no workflow uses `lycheeverse/lychee-action` anymore.
- Not run locally: the GitHub-hosted cache itself, which needs a runner. The script was run locally with the real
  lychee v0.24.2 (downloaded and verified by the script) on the root docs: 5277 links, 0 errors, exit 0, the same as
  the action. It was also run on a page with a broken link (exit 2) and on a page with no link (exit 1).
