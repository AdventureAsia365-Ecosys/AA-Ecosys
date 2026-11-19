# AA-1051 — Nhãn panel cho 48 mẫu T2 (S285)

Tác nhân: Claude Code (panel agent, $0, không gọi gateway, không AWS). Bản này chỉ ghi số liệu: không chép văn bản mẫu,
không ghi mã tour. Chi tiết từng phiếu và đoạn trích nằm ở thư mục riêng `.tmp-session/` (không commit).

## Kết quả

- Fixture mới: **1.7.0** (từ 1.6.0, 170 → 218 mẫu). Thêm **t2-021..t2-068** (48 mẫu, không bỏ mẫu nào).
- Nhãn 48 mẫu: **27 pass / light**, **21 fail / heavy** (không có as_is, không có fail light).
- Toàn bộ nhóm T2 sau merge: 31 pass, 37 fail (20 mẫu cũ: 4 pass, 16 fail).
- Phân chia (theo hash id, không phụ thuộc verdict): dev 18 (10 pass, 8 fail), cal 15 (9 pass, 6 fail),
  gate 15 (8 pass, 7 fail).
- `gate_by_writer` sau merge: **a1 = 26 (không đổi)**, **t2 = 20** (trước 5), t9_blog = 12, t9_social = 11.
- Người duyệt ghi trong fixture: "S285 agent panel (pending tech lead review)"; bước apply ghi thêm
  "disputes by the orchestrator rule (pending tech lead review)".

## Đồng thuận

Luật trạng thái: *agreed* khi verdict của verifier (đọc toàn bộ Master) trùng với đa số ba lens (facts, voice, reader).

| | Số mẫu | pass | fail |
|---|---|---|---|
| Đồng thuận ngay | 38 | 27 | 11 |
| Tranh chấp (lens 2-1 pass, verifier fail) | 10 | 0 | 10 |

Phiếu từng lens trên 48 mẫu: facts 35 pass / 13 fail, voice 45 / 3, reader 32 / 16, verifier 27 / 21.
Lens voice gần như luôn pass (chỉ fail 3 bản chép nguyên văn Master), nên đa số lens nghiêng về pass hơn verifier.

## Tranh chấp — quyết định theo luật điều phối (tech lead có thể đảo)

Luật (giống s1-018 ở S1): theo đa số lens chỉ khi lý do fail duy nhất của verifier là điều chính verifier đã coi là lỗ
hổng pipeline (không phải lỗi writer) ở mẫu khác cùng bộ; ngược lại theo verifier. Trong bộ này verifier chỉ miễn lỗi
cho những gì chép từ Master ("Master issue, not a writer fault"); không lý do fail nào của 10 mẫu tranh chấp thuộc loại
đó. Vì vậy **cả 10 theo verifier: fail / heavy**, ghi `status: agreed` với lý do bắt đầu bằng "Decision S285 ...".

| Fixture id | Split | Loại lý do fail của verifier |
|---|---|---|
| t2-033 | gate | Giọng thương hiệu không được áp (chép nguyên văn Master) |
| t2-049 | cal | Hứa dịch vụ không có trong Master; thêm quyền tiếp cận |
| t2-050 | cal | Sai tuyến trong tiêu đề ngày; bỏ bữa ăn đã bao gồm |
| t2-053 | cal | Bỏ chính sách "tự túc" khỏi mọi trường; hạng tàu, thời gian không có nguồn |
| t2-054 | dev | Thêm phương tiện, hoạt động, đặt sai địa điểm hoạt động |
| t2-056 | dev | Câu kết chuyến sai sự thật; thêm hoạt động |
| t2-057 | dev | Bỏ dòng bữa ăn ở mọi ngày |
| t2-063 | gate | Hoạt động có điều kiện viết như cố định |
| t2-065 | cal | Thêm hoạt động, quyền tiếp cận, tuyên bố "dễ cho trẻ" |
| t2-068 | gate | Thêm cách di chuyển, vị trí chỗ ngủ, hoạt động ăn uống |

## Điểm chưa nhất quán cần tech lead xem

Luật trên không quyết được các điểm này; nhãn hiện tại theo verifier, nhưng chính verifier chấm khác nhau giữa các mẫu:

1. **Bỏ dòng bữa ăn**: light ở t2-046, t2-066 nhưng fail ở t2-057 (và là một phần lý do fail của t2-050, t2-064).
2. **Cùng Master, cùng lỗi tiêu đề ngày + bỏ bữa sáng**: light ở t2-036, fail ở t2-050.
3. **Cùng Master, câu "kết thúc bằng" homestay**: light ở t2-021; ở t2-056 còn thêm một hoạt động nên fail vẫn đứng.

Nếu tech lead đảo một quyết định: sửa mục đó trong `panel-t2.json`, chạy lại `labels apply` rồi `labels merge` từ
1.6.0. Id và split GATE không đổi (chỉ verdict đổi), nên `gate_by_writer` giữ nguyên.
