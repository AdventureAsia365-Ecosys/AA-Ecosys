# Session Log — S182 (AA-Ecosys dev)

- **Ngày:** 2026-09-16
- **Agent:** Kiro
- **Chủ đề:** TripPlanner MAP/UI (Ms.Thư #4/#5 + nợ UI) — build/deploy hoàn chỉnh; dựng khung audit CIS data reset; MCP DB tunnel guide.
- **Trạng thái:** Hoàn tất phần TripPlanner (deployed). Audit CIS mới ở bước lập kế hoạch (chưa chạm DB).

---

## 1. Trạng thái

- Đầu phiên: đọc memory Notion S181 + log local + Linear → chỉ AA-588 (G5 OIDC) còn Backlog, mọi thứ khác Done. Nợ UI TripPlanner + 5 việc Ms.Thư chưa có issue.
- Nghiệp quyết: G5/AA-588 theo dõi 7 ngày rồi xóa sau. Phiên này làm nợ UI TripPlanner + việc Ms.Thư.
- Cuối phiên: TripPlanner MAP/UI đã deploy production. Audit CIS reset đã có epic + 8 sub-issue + tài liệu plan, chờ chạy G0 phiên sau.

## 2. Thay đổi CODEBASE

### AA-TripPlanner-Web (PR #46, squash-merge main, commit `525a674`)
- `backend/assembly/suggestions.py` — #5 suggest next place: blend taste (pgvector) + geography (khoảng cách km tuyệt đối tới stop cuối, ramp 150–1500km, weight 0.6/0.4). Helpers `_rank_norm`, `_geo_score`, `_last_stop_coord`, `_rerank_by_route`. Không anchor → degrade về taste order cũ.
- `backend/tests/test_assembly.py` — +3 test re-rank.
- `frontend/lib/useTrip.tsx` — thêm `previewCountry` + `setPreviewCountry`.
- `frontend/components/FilterChips.tsx` — country picker `<select>` → **custom listbox** (hover preview highlight; native `<option>` không bắn onMouseEnter — root cause nợ treo).
- `frontend/components/MapView.tsx` — effect highlight ưu tiên `previewCountry ?? filters.country`; thêm `TRIP_GATEWAY_SOURCE` + 3 layer (dot/✈/label) + dashed arc gateway→stop (#4 arrival/departure trên map).
- `frontend/lib/mapbox.ts` — thêm `ALL_GATEWAYS` + `nearestGateway` (dùng chung).
- `frontend/components/TripPanel.tsx` — bỏ định nghĩa trùng, import từ mapbox.ts. (Panel arrival/departure ĐÃ có sẵn từ trước.)
- Icon 6+2: xác nhận đã đủ 8 activity (schemas.py Enum ↔ ACTIVITIES ↔ ICONS), no code change.

### AA-Ecosys (repo gốc, chưa commit — sẽ do Nghiệp/phiên sau)
- `docs/db-access-ssm-tunnel.md` + `docs/db-tunnel.sh` (chmod +x) — hướng dẫn SSM tunnel qua bastion EC2 (Fargate không hỗ trợ port-forward-to-remote-host) + SQLTools.
- `.vscode/settings.json` — SQLTools connection `AA RDS (tunnel)` → localhost:5432.
- `docs/audit-cis-data-reset.md` — bản đồ audit (bảng giữ/xóa/thứ tự con→cha, pipeline A0-A3/T-series, TripPlanner dẫn xuất bậc-2, UI real/mock).
- `.gitignore` — thêm `docs/backups/`.

## 3. Thay đổi HẠ TẦNG
- **KHÔNG đụng hạ tầng** phiên này. Chỉ deploy Lambda code TripPlanner qua CI (OIDC).
- Deploy Lambdas run 35054357929 = success (browse + assembly, sha 525a674). Vercel prod deploy từ push main.

## 4. Bằng chứng verify
- Frontend: `next build` BUILD=0 (routes render), `tsc --noEmit`=0, `next lint`=0.
- Backend: full pytest **69 passed**.
- CI PR #46: Backend + Frontend + Vercel = SUCCESS; mergeStateStatus CLEAN.
- Sau merge main: Deploy Lambdas = success, CI = success.

## 5. Linear
- Project mới **AA_TripPlanner**: epic **AA-589** + sub AA-590 (#5), AA-591 (#4), AA-592 (hover), AA-593 (icon) — tất cả **Done**, PR #46 attach.
- Project mới **CIS Data Reset & Pipeline Rerun (Audit)**: epic **AA-594** + 8 sub-issue Backlog: G0 AA-595, G1 AA-596, G2 AA-597, G3 AA-598, G4 AA-599, G5 AA-600, G6 AA-601, cleanup(terminate bastion) AA-602.
- AA-588 (G5 OIDC) vẫn Backlog — theo dõi 7 ngày rồi xóa (Nghiệp quyết).

## 6. CÒN LẠI — việc đầu phiên sau (audit CIS)
- **G0 (AA-595) trước tiên:** RDS snapshot `aa-cis-dev-db` + dựng bastion EC2 (Nghiệp đã duyệt dựng, NHỚ terminate — AA-602) + tunnel + pg_dump theo schema về `docs/backups/`. Chặn mọi việc sau.
- Rồi G1 điều tra → G2 script+duyệt → G3 reset → G4 S1 → G5 atomize/social + rebuild TripPlanner extraction → G6 UI → cleanup.
- **Phạm vi tenant đã rõ:** KHÔNG có tenant thật, chỉ tenant test (giai đoạn dev, chỉ team AA/admin dùng) → G3 reset không cần chừa tenant nào. G1 vẫn nên xác nhận số liệu before.

## 7. Lưu ý kỹ thuật
- Terminal WSL trong phiên **treo giữa chừng** (chỉ echo lệnh, không thực thi) — cần reset terminal (đóng/mở) khi gặp. Cách chạy ổn: `cd /home/nghiep/... && cmd`; đọc stdout qua file trong app dir (không dùng `/tmp` — bị resolve tương đối workspace).
- `.venv` TripPlanner ở `apps/AA-TripPlanner-Web/.venv`; pytest = `cd backend && ../.venv/bin/python -m pytest`.
- Merge PR TripPlanner: repo này KHÔNG có branch protection kiểu AA-CIS-App → `gh pr merge --squash --delete-branch` được ngay khi CI xanh.
- COUNTRY_GATEWAY mới có 6 nước (Laos/Sri Lanka/South Korea/Nepal/Japan/India) → nước khác trỏ nhầm gateway gần nhất; follow-up bổ sung (ghi trong AA-591).
- RDS: `aa-cis-dev-db`, DB `aa_cis_dev`, user `aa_cis_admin`, secret `aa-cis/dev/rds`. Sentinel master tenant `00000000-0000-0000-0000-000000000001`.
