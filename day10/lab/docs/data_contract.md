# Data contract — Lab Day 10

Bản mô tả chi tiết cam kết chất lượng và cấu trúc dữ liệu của pipeline `kb_chunk_export`.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `policy_refund_v4` | Batch CSV Export | Chứa cửa sổ hoàn tiền cũ 14 ngày thay vì 7 ngày | Expectation `refund_no_stale_14d_window` -> HALT |
| `sla_p1_2026` | Batch CSV Export | Thiếu ngày hiệu lực, thiếu nội dung | Expectation `min_one_row` / `effective_date_iso_yyyy_mm_dd` -> HALT |
| `it_helpdesk_faq` | Batch CSV Export | Thông tin trùng lặp, thiếu ngày hiệu lực | Expectation `no_duplicate_doc_text_pairs` -> WARN |
| `hr_leave_policy` | Batch CSV Export | Xung đột phiên bản chính sách nghỉ phép (10 ngày phép của 2025 vs 12 ngày phép của 2026) | Expectation `hr_leave_no_stale_10d_annual` -> HALT |
| `access_control_sop` | Batch CSV Export | Tài liệu mới chưa được đăng ký trong allowlist hệ thống | Expectation `all_grading_sources_present` -> HALT |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| `chunk_id` | string | Có | Khóa chính duy nhất dạng ổn định: `{doc_id}_{seq}_{hash}` |
| `doc_id` | string | Có | Định danh tài liệu (thuộc `ALLOWED_DOC_IDS`) |
| `chunk_text` | string | Có | Nội dung văn bản đã chuẩn hóa và loại bỏ các tiền tố nhiễu |
| `effective_date` | date | Có | Ngày hiệu lực của văn bản dạng ISO `YYYY-MM-DD` |
| `exported_at` | datetime | Có | Ngày xuất dữ liệu dạng ISO `YYYY-MM-DDTHH:MM:SS` |

---

## 3. Quy tắc quarantine vs drop

- **Phân loại lỗi:**
  - **Quarantine (Cách ly):** Áp dụng cho các record có cấu trúc hợp lệ nhưng vi phạm các ràng buộc nghiệp vụ hoặc schema (ví dụ: ngày hiệu lực không đúng định dạng, sai allowlist `doc_id`, thiếu thời điểm xuất dữ liệu `exported_at`, thông tin cũ/stale, hoặc trùng lặp văn bản).
  - **Drop (Bỏ qua):** Record bị bỏ hoàn toàn nếu rỗng/thiếu cả thông tin định danh và nội dung (`doc_id` rỗng, `chunk_text` rỗng sau chuẩn hóa).
- **Quản lý dữ liệu quarantine:**
  - Record bị cách ly được ghi nhận vào file `quarantine_<run-id>.csv` kèm cột `reason` và `metric_impact`.
  - Đội ngũ Data Quality sẽ review hàng tuần và phối hợp với Owner của hệ thống nguồn để sửa dữ liệu bẩn và import lại ở chu kỳ sau.

---

## 4. Phiên bản & canonical

- **Chính sách Hoàn tiền (Refund Policy):** Source of truth chính thức là tài liệu [policy_refund_v4.txt](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/data/docs/policy_refund_v4.txt). Bất cứ nội dung nào nhắc tới "14 ngày làm việc" đều là thông tin stale của phiên bản cũ và được tự động thay thế bằng "7 ngày làm việc".
- **Chính sách Nghỉ phép (HR Leave Policy):** Phiên bản áp dụng cho năm 2026 yêu cầu nhân viên dưới 3 năm kinh nghiệm có **12 ngày phép năm**. Phiên bản 2025 với **10 ngày phép** được coi là lỗi thời (stale) và bị loại bỏ khỏi luồng clean để tránh Agent RAG trả lời sai.
