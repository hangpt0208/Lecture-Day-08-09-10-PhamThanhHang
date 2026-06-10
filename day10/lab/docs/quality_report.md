# Báo cáo Chất lượng Dữ liệu (Quality Report) — Lab Day 10

**run_id:** `2026-06-10T09-33Z`  
**Ngày:** 2026-06-10

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (Baseline) | Sau (Cải tiến) | Ghi chú |
|--------|------------------|----------------|---------|
| `raw_records` | 247 | 247 | Tổng số lượng record đầu vào |
| `cleaned_records` | 40 | 30 | Giảm do lọc bỏ các noisy duplicates và stale policies |
| `quarantine_records` | 207 | 217 | Tăng do cách ly thêm các bản ghi stale/nhiễu |
| **Expectation halt?** | **YES** | **NO** | Baseline bị dừng do xung đột phép năm của HR policy |

---

## 2. Before / after retrieval

Bằng chứng so sánh kết quả truy vấn thông tin giữa khi dữ liệu bị lỗi (Inject Corruption) và sau khi chạy qua pipeline chuẩn đã cải tiến:

### Câu hỏi hoàn tiền (`gq_d10_01` - refund window)
- **Truy vấn:** *"Theo chính sách hoàn tiền hiện hành, khách hàng có tối đa bao nhiêu ngày làm việc để gửi yêu cầu hoàn tiền sau khi đơn được xác nhận?"*
- **Trước (Inject Corruption - `after_inject_bad.csv`):**
  - `top1_doc_id`: `policy_refund_v4`
  - `contains_expected`: `no` (Không chứa "7 ngày")
  - `hits_forbidden`: `yes` (Chứa thông tin cũ "14 ngày làm việc")
  - `top1_preview`: *"Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc..."*
- **Sau (Standard Clean - `after_fix_eval.csv`):**
  - `top1_doc_id`: `policy_refund_v4`
  - `contains_expected`: `yes` (Chứa đúng "7 ngày làm việc")
  - `hits_forbidden`: `no` (Không còn "14 ngày làm việc")
  - `top1_preview`: *"Chính sách hoàn tiền (policy refund v4): Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày làm việc..."*

### Câu hỏi chính sách nghỉ phép HR (`gq_d10_09` - versioning HR)
- **Truy vấn:** *"Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm theo chính sách HR 2026?"*
- **Trước (Baseline):**
  - `top1_doc_id`: `hr_leave_policy`
  - `contains_expected`: `no` (Bị nhiễu bởi các tài liệu cũ 2025)
  - `hits_forbidden`: `yes` (Chứa thông tin cũ "10 ngày phép năm")
- **Sau (Cải tiến):**
  - `top1_doc_id`: `hr_leave_policy`
  - `contains_expected`: `yes` (Trả về đúng "12 ngày phép năm" theo chính sách 2026)
  - `hits_forbidden`: `no` (Đã lọc bỏ hoàn toàn các record 2025 chứa "10 ngày phép")

---

## 3. Freshness & monitor

- **Kết quả `freshness_check`:** `FAIL`
- **Chi tiết:**
  - `latest_exported_at`: `2026-04-11T00:00:00`
  - `age_hours`: `1449.556` (giờ)
  - `sla_hours`: `24.0` (giờ)
- **Giải thích:** Tập dữ liệu CSV mẫu (`policy_export_dirty.csv`) có thời điểm xuất cuối cùng là tháng 04/2026. Do thời gian hiện tại của hệ thống là tháng 06/2026, khoảng cách thời gian vượt quá SLA 24 giờ là hoàn toàn chính xác. Trong thực tế vận hành, SLA 24 giờ giúp phát hiện ngay lập tức nếu tiến trình export dữ liệu tự động từ DB nguồn bị gián đoạn quá một ngày.

---

## 4. Corruption inject (Sprint 3)

- **Kịch bản Inject:** Sử dụng cờ `--no-refund-fix --skip-validate` khi chạy pipeline.
- **Mô tả hành vi:** Bỏ qua quy tắc chuyển đổi hoàn tiền từ 14 ngày về 7 ngày. Việc này giữ nguyên dữ liệu lỗi thời của chính sách hoàn tiền trong collection.
- **Cách phát hiện:** Lượt chạy kích hoạt cảnh báo lỗi `refund_no_stale_14d_window` (FAIL) trong báo cáo validations, và khi chạy evaluation `eval_retrieval.py` ghi nhận `hits_forbidden=yes` cho các câu hỏi hoàn tiền.

---

## 5. Hạn chế & việc chưa làm

- Chưa tích hợp cơ chế tự động gửi thông báo trực tiếp qua Webhook Slack/Teams khi kiểm tra Freshness bị FAIL.
- Phép so sánh trùng lặp dữ liệu (`seen_text`) hiện tại đang nhạy cảm với các ký tự hoa thường và dấu câu; có thể nâng cấp bằng thuật toán MinHash/LSH để phát hiện trùng lặp mờ (fuzzy duplicate).
