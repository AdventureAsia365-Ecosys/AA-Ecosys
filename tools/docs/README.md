# Docs lint tools (AA-888)

The checks behind [`.github/workflows/docs-lint.yml`](../../.github/workflows/docs-lint.yml). The rules they enforce
are in [`docs/STYLE.md`](../../docs/STYLE.md).

| Tool | Checks | Level in root |
|---|---|---|
| `check_frontmatter.py` | Front-matter of every `docs/**/*.md` page that has one validates against `docs/templates/frontmatter.schema.json`; catalog IDs are unique (templates excluded). `--freshness-report` writes the weekly report. | error (freshness: warning) |
| `check_adr_index.py` | Each `docs/adr/NNNN-*.md` states a status (Proposed, Accepted, Deprecated, Superseded, Rejected) and is linked from `docs/adr/README.md`. | error |
| `check_docs_text.py aws-multiline` | No `aws ...` command continued with a backslash in `docs/`, `skill/`, `.kiro/steering/`, `.claude/` (journals excluded). | error |
| `check_docs_text.py resource-ids` | No `sg-`/`subnet-`/`vpc-` IDs, standalone 12-digit account IDs, ARNs with an account, user-pool IDs or API Gateway hosts in `docs/` prose (journals, `docs/onboarding.md` and generated pages excluded). | warning (`--mode error` for public repos) |
| `lychee.toml` | Internal links, offline. | error |

Journals keep their history as written and are out of scope: `docs/sessions/`, `docs/audits/`,
`docs/implementation-notes/`, `docs/backlog/`, `docs/research/`, `docs/calib/`. To skip one line on purpose, put
`docs-lint: ignore` on it (an HTML comment works).

## Run locally

From the repo root:

```bash
python3 -m pip install -r tools/docs/requirements.txt
python3 -m unittest discover -s tools/docs -p 'test_*.py'
python3 tools/docs/check_frontmatter.py
python3 tools/docs/check_adr_index.py docs/adr
python3 tools/docs/check_docs_text.py aws-multiline
python3 tools/docs/check_docs_text.py resource-ids --mode warn
python3 tools/docs/check_frontmatter.py --freshness-report .tmp-session/freshness.md
```

Link check, with a [lychee](https://github.com/lycheeverse/lychee) binary on the PATH:

```bash
lychee --config tools/docs/lychee.toml 'docs/**/*.md'
```

The other repos can run `check_adr_index.py` and `check_docs_text.py` with `--root <repo>`: both are stdlib only.

## Copies in AA-Booking and AA-CIS-Infra

AA-Booking and AA-CIS-Infra vendor these files in their own `tools/docs/` (public / separate repos cannot read this
private one from CI). `docslib.py`, `check_docs_text.py`, `check_adr_index.py`, `check_frontmatter.py`,
`test_docs_tools.py`, `lychee.toml` and `requirements.txt` must stay byte-identical in all three repos; only each
README is repo-specific. Options used only by those repos, harmless here:

- `check_docs_text.py ... --all` scans every tracked Markdown file (minus journals) instead of the default scope.
- `check_docs_text.py resource-ids --mode warn --block vpc,apigw` keeps the listed kinds failing in warn mode
  (kinds: `vpc`, `arn`, `user-pool`, `apigw`, `account`).
- `check_frontmatter.py` also validates a `CONTEXT.md` at the repo root; this repo has none.

Change a rule here first, then copy the seven files to both repos in the same session, and check from the workspace
root:

```bash
for f in docslib.py check_docs_text.py check_adr_index.py check_frontmatter.py test_docs_tools.py lychee.toml requirements.txt; do cmp tools/docs/$f apps/AA-Booking/tools/docs/$f; cmp tools/docs/$f infra/AA-CIS-Infra/tools/docs/$f; done
```
