# S286 lane l11: AI disclosure wording as an admin setting, live check (20/11/2026 ~05:05Z)

Shipped: CIS #1621 `c6154c99` (migrations 463 setting `cis.content.ai_disclosure`, 464 `publish_log.sent_message`),
CIS #1622 `e29ee061` (wording read from the setting, Facebook retry by the sent text), AA-Partner #372 `44daca2e`
(My Content export reads the wording from CIS). CIS `/health/ready`: schema_version 464, git_sha `e29ee061`.
Identity: the E2E owner of the synthetic agency `pilot-rehearsal-01` (saved UAT state). Cost: 0 USD, no model call.

| # | Check | Result |
|---|---|---|
| 1 | `GET /api/tenant/v1/content-writing/ai-disclosure` through the agency BFF | **PASS** 200, `{"text": {"en": "This content was created with the help of AI.", "vi": "Nội dung này được tạo với sự hỗ trợ của AI."}, "social_tag": "#AIgenerated"}` |
| 2 | Plain-text export of the test blog piece | **PASS** 200, `X-AI-Generated: true`, ends `---` / the disclosure line / `AI-Content:` |
| 3 | Facebook test Page: publish the test piece, read the post back by Graph | **PASS** message (1409 chars) ends with `"\n\nThis content was created with the help of AI. #AIgenerated"` built from the setting |
| 4 | `acp_shared.publish_log.sent_message` of that publish row (ECS exec, length + tail only) | **PASS** 1409 chars, same tail as the post |
| 5 | Clean-up | **PASS** unpublished (200); Graph read of the post answers 400 (gone) |

Not tested live: an approved rewording end to end (maker-checker needs a second staff approver; covered by unit tests
`test_aa1168_disclosure_wording_in_use.py`: wording change, vi line, 422 / 409 refusals, retry after a wording change),
and a fresh CSV / XLSX download in the studio UI (the BFF read it uses is check 1; export covered by vitest).
