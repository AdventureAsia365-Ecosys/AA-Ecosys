# AA-1166 — S294 doc follow-ups (lane l27-docs-followups, root)

Docs only. Applies the root doc follow-ups the other S294 lanes named in their PRs (CIS visual run, CIS writer note,
the AI red-team in CIS, AA-Partner and AA-TripPlanner-Web, the TripPlanner error bodies and redirect, the shared map
engine). No code, no setting, no route.

## Decisions

- **AI Use Register v1.17.** The writer note control goes into the "Human gate" cell of the `s1_generate` and
  `t2_generate` rows (the register has no separate controls column per row) and into the OWASP LLM05 controls; the
  AI red-team method goes into the LLM01 controls, where the AA-1167 trap set already sits. The `s1_generate` row says
  "S1 v1 graph": the S1 writer v2 keeps its own parser and does not run the new extractor (CIS notes
  `AA-1166-t2-note-before-json.md`).
- **No result of any red-team run** on this public page: only the method, the stages and where the code lives. The
  reports stay in the private ISMS evidence location.
- **`ai-gateway.md` unchanged.** It does not describe reply parsing (the writer note is a writer-side parse, not a
  gateway step), so the lane's conditional item does not apply.
- **Skill pages stay in Vietnamese**, like the rest of `skill/aa-ui-verify` and `skill/aa-ecosys-repos`.

## Changed

- `docs/architecture/ai-use-register.md`: v1.17 note, two row cells, LLM01 and LLM05 controls, change log row,
  `AA-1166` in `related`.
- `skill/aa-ui-verify/SKILL.md` §3 step 2: the CIS visual run page list (every dynamic admin route, `EXCLUDED` empty,
  fixed path or `openFirst`, router-push rows opened by `rowTestId` + Enter, skips for an empty list or a page the
  read-only E2E role may not open).
- `skill/aa-ecosys-repos/references/tripplanner.md`: the bodiless 307 of the bare agency slug, the BFF 5xx body
  `{error, request_id}`, the shared map engine (canonical in TripPlanner, guarded byte copy in AA-Partner), and the
  operator-only red-team invoke.

## Tradeoffs

- `last_reviewed` of the register is not raised: only the rows named here were checked, not the whole page.
- The pending generated-block refresh (`gen_sections.py` warns that the facts snapshot moved on) is left to its own
  docs PR, so this lane does not touch generated files other lanes may also refresh.

## Should know

- `skill/` files are outside the markdownlint scope of the docs check; two older MD040 findings in
  `skill/aa-ui-verify/SKILL.md` (fenced blocks without a language) predate this change.
