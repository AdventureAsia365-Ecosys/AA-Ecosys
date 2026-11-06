# Artifact links (claude.ai pages)

One place for every claude.ai page the program uses, so links survive a change of claude.ai account. Machine-readable copy: [`registry.json`](registry.json).

## Rules

- **Update in place.** Publish with `url` = the link below (read the page first in a new conversation). The pages are shared with the team, so any team account with writer access can update them. Never create a new page because the account changed.
- **If a write is refused,** ask the tech lead before making a new page; then add the new link here and move the old one to *Superseded*.
- **Share keys stay out of this repo.** The repo is public: a link with `?sk=` opens the page for anyone who has it. Keep such links in private notes only.
- **New page:** add a row to `registry.json` and this table in the same PR as the audit or doc that uses it.

## Active pages

| Page | Link | What it is | Source in repo |
|---|---|---|---|
| AA_Ecosys Master Plan | <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF> | Kế hoạch tổng thể + tab Phiên; cập nhật đầu phiên, sau mỗi bước lớn, cuối phiên | `docs/backlog/tracker/ (index.html + plan.json + sessions/)` |
| Kiến trúc AWS AA_Ecosys | <https://claude.ai/artifact/HrLRN1M3PyKKRjm5VJkvKV> | Sơ đồ tầng AWS từ Internet tới DB (acc2) | `docs/audits/2026-11-06-S271-aws-architecture/index.html` |
| Chốt chất lượng viết S271 | <https://claude.ai/artifact/YZzbttV86QkzHssvsfkAbd> | 16 quyết định ADR 0020 (db `decisions`) | `docs/audits/2026-11-06-S271-writing-quality-audit/` |
| Danh mục báo cáo | <https://claude.ai/artifact/Jiz8KaJiWrpdrvi5eJWWJ4> | Trang đọc mọi báo cáo audit | `docs/audits/2026-10-29-S258-report-catalog/` |
| AA-Ecosys Engineering Handbook | <https://claude.ai/artifact/Lg8MqNQcgkbsqaLp81qNwp> | Sổ tay kỹ thuật | `docs/ (handbook)` |
| AI gateway thiết kế v2 | <https://claude.ai/artifact/Mhw2JBwZQBW5DEzpuPG1pc> | Trang duyệt thiết kế gateway (ADR 0009) | `docs/audits/2026-10-31-S261-ai-gateway-design-v2/` |
| AA-CIS Design System v2 | <https://claude.ai/artifact/FEWjBR5UfmvHFSesjL6nR3> | Design system / kit | `docs (ADR 0016)` |

## Superseded

| Old link | Use instead |
|---|---|
| <https://claude.ai/artifact/2VSP2stGG1TF7uXvqgQTUY> | <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF> |
| <https://claude.ai/artifact/XzuEARCJJnCJj6s5ckEpGX> | <https://claude.ai/artifact/HrLRN1M3PyKKRjm5VJkvKV> |
| <https://claude.ai/artifact/6y5NHZ2rx1Yb7euNifHYeY> | <https://claude.ai/artifact/YZzbttV86QkzHssvsfkAbd> |

## Archive (one-off decision and review pages, read-only history)

| Page | Link | Cited in |
|---|---|---|
| - **Report:** `docs/audits/2026-10-10-S223-jev-audit.html` (root repo) · artifact https:// | <https://claude.ai/artifact/8A5XBeeUU5n7B8potPMt5q> | `docs/linear-export/cis-core-pipeline-llm-platform/AA-756.md:90`, `docs/sessions/2026-10-10-S223-n7-distinct-jobs-s1-wave-jev-audit.md:32` |
| - 16 đề xuất. Trang duyệt: https://claude.ai/artifact/5srRKGxXrdiADV6u13niAH, Nghiệp **c | <https://claude.ai/artifact/5srRKGxXrdiADV6u13niAH> | `docs/sessions/2026-10-20-S245-quality-system-golden-set-codeql-crm-research.md:102`, `docs/sessions/2026-10-20-S245-quality-system-golden-set-codeql-crm-research.md:128` |
| - Catalogue page of every Drive video (private artifact): https://claude.ai/artifact/71GWJ | <https://claude.ai/artifact/71GWJcHwyzdm88XjpKp6V6> | `docs/linear-export/data-platform-schema-ops-scale/AA-1021.md:91` |
| - Data standards v1.0 written (wf_7f34466b-0c8): docs/architecture/data-standards/{README, | <https://claude.ai/artifact/R1YLp4i1QCt3kjnKd6yvvJ> | `docs/audits/2026-10-14-S237-lane-backlog/00-orchestrator-journal.md:68`, `docs/sessions/2026-10-15-S237-chuoi-lane-5-repo-rls-retention-data-standards.md:8` |
| - Ecosystem blueprint published: https://claude.ai/artifact/Hz5bn9ryLDToqiNU7vrHpt (source | <https://claude.ai/artifact/Hz5bn9ryLDToqiNU7vrHpt> | `docs/audits/2026-10-14-S235-ecosystem-team-pilot/00-orchestrator-journal.md:64`, `docs/audits/2026-10-14-S235-ecosystem-team-pilot/README.md:9` |
| - Trang duyệt: https://claude.ai/artifact/9mmgckVoU9BHQ3dG6woEuG. | <https://claude.ai/artifact/9mmgckVoU9BHQ3dG6woEuG> | `docs/sessions/2026-10-20-S245-quality-system-golden-set-codeql-crm-research.md:95` |
| - `aws-llm-model.html`: https://claude.ai/artifact/5zccrpwjZ31c2XtiP4HRfu (private, clau | <https://claude.ai/artifact/5zccrpwjZ31c2XtiP4HRfu> | `docs/audits/2026-10-31-S261-aws-bedrock-org-access/README.md:488` |
| - `llm-gateway.html`: https://claude.ai/artifact/3Sx24UxNAHj7NnqR2gsPpf (private, claude | <https://claude.ai/artifact/3Sx24UxNAHj7NnqR2gsPpf> | `docs/audits/2026-10-31-S261-llm-capacity-plan/README.md:737` |
| - `org-accounts.html`: https://claude.ai/artifact/TXwm33B2PZ8xx67q6H8aHv (private, claud | <https://claude.ai/artifact/TXwm33B2PZ8xx67q6H8aHv> | `docs/audits/2026-10-31-S261-llm-capacity-plan/README.md:736` |
| - `page.html`: https://claude.ai/artifact/Rgw1AnJotY3iLtyqnUcw97 (private, claude.ai acc | <https://claude.ai/artifact/Rgw1AnJotY3iLtyqnUcw97> | `docs/audits/2026-10-31-S261-crm-progress-video-plan/README.md:216`, `docs/linear-export/partner-crm-aa-partner/AA-1014.md:25` |
| - `review.html`: https://claude.ai/artifact/WZyv9k6EHG559tCBm3DZZz (private, claude.ai a | <https://claude.ai/artifact/WZyv9k6EHG559tCBm3DZZz> | `docs/audits/2026-10-31-S261-architecture-review/README.md:989` |
| AA Ecosys CI | <https://claude.ai/artifact/UG5UJXbwrXJRNq4DTFLkhq> |  |
| AA-729 nhãn golden set | <https://claude.ai/artifact/FSR7H3tiZE25Pn3irbetnJ> |  |
| AA-847 tuyến và gộp trùng | <https://claude.ai/artifact/EH6RFt5Wo8pHx7SJ2sBn29> |  |
| AA-Partner giao diện | <https://claude.ai/artifact/2mCk7BrajpTpLEFao7PRt3> | `docs/audits/2026-10-21-S246-jira-drafts/README.md:52`, `docs/audits/2026-10-21-S246-jira-drafts/README.md:52` |
| Advisory page for Nghiệp (Vietnamese): https://claude.ai/artifact/QUqBMVfkpyeaSWwU8qiARG | <https://claude.ai/artifact/QUqBMVfkpyeaSWwU8qiARG> | `docs/audits/2026-10-12-S232-t9-social-audit/README.md:3`, `docs/sessions/2026-10-12-S232-aa768-aa764-aa763-audit-t9.md:42` |
| Bảng câu hỏi CRM đại lý | <https://claude.ai/artifact/SJD31VTYU1YNP98fyePMNT> |  |
| Bộ hồ sơ pháp lý AA | <https://claude.ai/artifact/7rCi74LYtgacopJwNZTE2d> |  |
| CRM kỹ thuật v2.1 | <https://claude.ai/artifact/QHJ6K2az7jGGMRUznXgrg9> |  |
| CRM thêm ý Tern TravelJoy | <https://claude.ai/artifact/DPRWweXAwKH9Wp41mRgW6W> |  |
| CRM v2.2 làm gọn | <https://claude.ai/artifact/8BhT3B2C8qQcM7zVHDjxpK> |  |
| CRM đại lý thiết kế v3 | <https://claude.ai/artifact/UQ7XHmCouUsH9QZFprHTwd> |  |
| Chưa soạn nháp Jira trong S265: tech lead yêu cầu "nháp jira gom qua phiên tiếp theo" (03/ | <https://claude.ai/artifact/S9JUSxTAdsULth39qHXQJN> | `docs/audits/2026-11-03-S265-close/jira-drafts.md:3`, `docs/audits/2026-11-03-S265-ecosystem-restructure/ARTIFACT.md:3` |
| Design (approved direction, mockups): [https://claude.ai/artifact/Hsr5SaBRNS7AxgRdoDhBAx]( | <https://claude.ai/artifact/Hsr5SaBRNS7AxgRdoDhBAx> | `docs/linear-export/cis-portal-admin-tenant-ui/AA-752.md:27`, `docs/linear-export/cis-portal-admin-tenant-ui/AA-752.md:27` |
| Design page (private artifact): [https://claude.ai/artifact/AgTQX7AwiRYAPj2SSYGjsX](https | <https://claude.ai/artifact/AgTQX7AwiRYAPj2SSYGjsX> | `docs/linear-export/cis-core-pipeline-llm-platform/AA-1042.md:42`, `docs/linear-export/cis-core-pipeline-llm-platform/AA-1042.md:42` |
| FAQ question check | <https://claude.ai/artifact/FkGxnXJuBCu7iJx7So58MK> |  |
| Hệ thống viết tự học | <https://claude.ai/artifact/LAM1LXGEQq9nCiRSkJCUNm> |  |
| OpenBA-Kit cho AA | <https://claude.ai/artifact/W4CA57NztrD39V5VdUGcs8> |  |
| Partner CRM Spec | <https://claude.ai/artifact/HpHJqSqVJSkdZd3FsPhMaX> |  |
| Photo request for AA marketing (Phase C brief) | <https://claude.ai/artifact/KjJJetZqq53KgJVNkSHmJm> | `docs/linear-export/tripplanner-aa-booking/AA-689.md:125`, `docs/sessions/2026-09-29-S202-embeddings-jobs-ui-kan90-tour-graph-planner.md:71` |
| S218 A-series pipeline audit | <https://claude.ai/artifact/BuaUQnyYeNYn9LSBxxyY1m> |  |
| S248 Decision Desk | <https://claude.ai/artifact/6MTgUdkyb1eVbEzeVWH7gH> | `docs/sessions/2026-10-23-S248-tour-liveness-b2b-secret-scan-erasure-drill-writer-decision.md:20` |
| Tenant CRM v2 | <https://claude.ai/artifact/KgdjgAVf77xCG4r4KunPsJ> |  |
| Trang duyệt (52 issue, milestone, lịch phiên, 3 câu hỏi; lựa chọn lưu trong db của artifac | <https://claude.ai/artifact/PZeVUNY6GeAP1w3frv2oXK> | `docs/audits/2026-11-03-S265-plan-issue-review/ARTIFACT.md:3` |
| `docs/audits/2026-11-03-S266-tripplanner-tenant-addons/` (https://claude.ai/artifact/HYrj | <https://claude.ai/artifact/HYrjWyt2tSqNoNpAyy5Pn8> | `docs/sessions/2026-11-03-S266-r1-control-plane-ai-marking-gate.md:41` |
| adventure.asia làm thước S1 | <https://claude.ai/artifact/FY4DWyQTwVm5c4Qcf4mQo6> |  |
| https://claude.ai/artifact/5QtvFweK4LHaMwF3HfXDok | <https://claude.ai/artifact/5QtvFweK4LHaMwF3HfXDok> | `docs/audits/2026-11-02-S264-close/jira-drafts.md:163`, `docs/sessions/2026-11-02-S264-gateway-leftovers-tenant-writing-sidebar-gameday.md:95` |
| https://claude.ai/artifact/MQtWM3o23Tit1tzvJ4D3ko, gitleaks AA-ACP-App); | <https://claude.ai/artifact/MQtWM3o23Tit1tzvJ4D3ko> | `docs/sessions/2026-10-17-S241-sdlc-admin-console-x1-security.md:10` |
| sánh đại lý): https://claude.ai/artifact/6XpQ8YUU7w7HsZ9AoGfnRb. Điều khoản hợp đồng của | <https://claude.ai/artifact/6XpQ8YUU7w7HsZ9AoGfnRb> | `docs/audits/2026-10-29-S258-aws-org-blueprint/README.md:20`, `docs/linear-export/data-platform-schema-ops-scale/AA-1002.md:41` |
| Đánh giá câu hỏi Jev | <https://claude.ai/artifact/8QcPZJu7Ww5D5MEs35GdaP> |  |
