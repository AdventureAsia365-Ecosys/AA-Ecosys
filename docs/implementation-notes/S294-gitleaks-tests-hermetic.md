# S294: hermetic gitleaks resolver tests (root)

An S293 lesson follow-up. Tests and docs only: the resolver's behaviour does not change.

## Decisions

- The S282 resolver step (the mise install of the pin under `$MISE_DATA_DIR`, `$XDG_DATA_HOME/mise` or
  `~/.local/share/mise`) made two root tests depend on the machine. On a machine with gitleaks 8.30.1 installed
  through mise:
  - `tools/github/test_ship_open_prs.py` `test_gitleaks_scans_the_branch_with_the_base_rules_before_any_push` met
    "unexpected command: [.../mise/installs/gitleaks/8.30.1/gitleaks, version]" in the FakeRunner;
  - `scripts/pre-push.sh --self-test` "gitleaks resolution (shim only)" found the real install instead of nothing, and
    so `tools/github/test_git_env_isolation.py` `test_prepush_script_drops_them_too` went red too.
  Both now point HOME at a temp dir and clear `MISE_DATA_DIR` / `XDG_DATA_HOME` (`OpenTest.setUp` for the whole
  class; the self-test subshells). Git stays hermetic through `ship_fakes.GIT_ENV` (`GIT_CONFIG_GLOBAL=/dev/null`),
  so moving HOME does not change git.
- Each test gained the positive case it lacked: a mise install of the pin inside the fake HOME wins over the broken
  shim on PATH.

## Changed

- `tools/github/test_ship_open_prs.py`, `scripts/pre-push.sh` (self-test only), `tools/github/README.md` (the order
  now names the mise install step and the CIS port).

## Tradeoffs

- The tests could instead patch `gitleaks_resolve.mise_install`. Isolating the environment covers every lookup the
  resolver makes, including ones added later.

## Should know

- The pre-push that blocked pushes with "gitleaks unreadable" (S284, S289, S293 lessons) is the AA-CIS-App hook, not
  the root one: the root hook already used this resolver. The CIS fix (a bash port of the same order) ships in the
  CIS PR of the same lane.
