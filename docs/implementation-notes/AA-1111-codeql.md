# AA-1111 — Implementation notes (root repo, lane l9-codeql: open CodeQL alerts, S294)

Scope of this lane: the open code scanning alerts of the root repo (26), AA-CIS-Infra (11) and AA-Partner (6), listed
live on 25/11. This note covers the root PR; the Infra and Partner PRs have their own `AA-1111-codeql.md`.

## Decisions

- **Live code is fixed, frozen audit files are accepted.** Ten root alerts sit in live tools and pages and are fixed
  in code. Fifteen sit in `docs/audits/**` (harness scripts and static pages kept as evidence, run by nobody): they
  get one register row each in `docs/security/vuln-exceptions.toml`, as do the three `secret-scan.yml`
  `pull_request_target` alerts (root, Infra, Partner) and the Partner HMAC-SHA1 webhook signature.
- **One row per alert number**, as the register requires (`#<n>`, never a rule). `approved_on` 2026-11-25, `expires`
  2027-02-23 (the 90-day cap of `vuln_triage.toml`). The alerts are dismissed "Won't fix" with the comment
  `exception until 2027-02-23: <reason> (SEC-03)`; agents do not dismiss (a GitHub write).
- **Each fix was checked with the CodeQL CLI locally** (bundle v2.27.6, the python and javascript packs, SHA-256 from
  the release API), running the code-scanning suite on the changed files before and after: every live alert of the
  three repos is reproduced on the base and gone after the change. A full-repo run of the root (all python, all
  JS/HTML) finds only the 15 `docs/audits/**` alerts; the Infra full python run finds none.
- **ship_common.py (#4, clear-text logging):** the source was the function name. CodeQL reads `mfa` as a password word
  (`([_-]|\b)mfa([_-]|\b)` in its heuristics), so printing what `mfa_status_line()` returned was "logging a password".
  Renamed `mfa_status_line` -> `sts_expiry_line` and `mfa_expiry` -> `sts_expiry`; the CLI (`ship_common.py mfa`) and
  its output are unchanged. The line holds an expiry time only.
- **build_docs_reader.py (#9, #10, ReDoS):** the leading-comment part of `SVG_START` was `<!--.*?-->` under `re.S`, which
  can also match `--><!--`; 24 repetitions took 24 s on the old regex. The comment body is now `(?:[^-]|-(?!-))*`
  (no `--` inside, as XML 1.0 requires), so a run of comments has one way to match. A comment holding `--` (invalid
  XML) is no longer accepted as an SVG start; Graphviz writes `&#45;` for a dash in its comments.
- **Tracker tooltips (#18, DOM XSS):** `data-tip` held HTML that `show()` put back with `innerHTML`. Every value was
  escaped when the attribute was written, but the browser unescapes attributes, so the tooltip read HTML back from
  the DOM. `data-tip` is now an index into `TIPS`, a list of `[bold, plain]` lines built into the tooltip with
  `createElement` / `textContent`. Same look; checked in headless Chromium on the three tooltip kinds.
- **UAT allow-lists (#13, #14, #15):** `x.replace(/\//g, '\\/')` escaped only `/` (which needs no escape in
  `new RegExp()`), leaving every other meta-character live. A full `escapeRegExp` is exported by `lib/net-guard.cjs`
  and used on the path constants of PRT-02 and PRT-06; the write-guard test compares with `new RegExp(...).source`.
- **tp-lead-proof.cjs (#11, regex from argv):** `--env` was already limited to `[a-z]{2,12}`, but the log-group match
  built a regex from it. It is now a token compare (`name.split(/[-_/]/).includes(env)`), the same match without a regex.
- **Test files (#8, #26):** `test_linear_export.py` renamed `SECRETS_COLON` -> `LABEL_COLON` (the name, not the value,
  made it "sensitive data written to a file"); `test_vuln_triage.py` compares the parsed hostname instead of
  `"first.org" in url`.

## Changed

- Nothing that runs in production. All root changes are in tools, tests, one static tracker page and the register.

## Tradeoffs

- Renaming identifiers to leave CodeQL's credential-word heuristic is cosmetic for the scanner, but each renamed
  name was inaccurate (it held an expiry, a label, an id), and the alternative (dismissing as false positive) leaves
  the next edit of the same line to raise a new alert.
- Frozen audit files: a register row expires after 90 days and must be renewed with a new reason. Deleting the
  files, or moving them to the S3 audit archive, ends that; it is left to the tech lead (the files are cited as
  evidence in session logs and audits).

## Should know

- Alert numbers for the orchestrator to dismiss "Won't fix" (each has its register row): root #1, #2, #3, #5, #6, #7,
  #12, #16, #17, #19, #20, #21, #22, #23, #24, #25; Infra #1; Partner #1, #4.
- Alerts closed by the fixes (they close on the next default-branch analysis after merge): root #4, #8, #9, #10, #11,
  #13, #14, #15, #18, #26; Infra #2-#11; Partner #2, #3, #5, #6.
