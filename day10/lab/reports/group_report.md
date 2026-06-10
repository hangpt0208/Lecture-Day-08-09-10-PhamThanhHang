# Báo Cáo Dự Án (Cá Nhân) — Lab Day 10: Data Pipeline & Data Observability

**Người thực hiện:** Phạm Thanh Hằng  
**MSSV/Email:** hangpt0208@company.internal  
**Ngày nộp:** 2026-06-10  
**Repo:** hangpt0208/Lecture-Day-08-09-10-PhamThanhHang  

---

## 1. Pipeline tổng quan

- **Nguồn raw:** Batch CSV export `data/raw/policy_export_dirty.csv` chứa 247 record từ 5 nguồn dữ liệu khác nhau bao gồm: `policy_refund_v4`, `sla_p1_2026`, `it_helpdesk_faq`, `hr_leave_policy`, và `access_control_sop` (nguồn mới đăng ký).
- **Luồng hoạt động:** Tiến trình thực hiện tải dữ liệu thô, loại bỏ các ký tự nhiễu tiền tố, chuẩn hóa ngày tháng hiệu lực và ngày xuất dữ liệu, lọc bỏ các dòng stale/conflict version, loại bỏ trùng lặp, chạy bộ kiểm tra chất lượng (Expectations), embed dữ liệu đã làm sạch vào ChromaDB collection `day10_kb` bằng model `all-MiniLM-L6-v2`, đồng thời xuất báo cáo manifest và kiểm tra freshness SLA.

**Lệnh chạy một dòng:**
```bash
.venv\Scripts\python etl_pipeline.py run
```
**Cách tìm run_id:** `run_id` được sinh tự động theo định dạng UTC timestamp `YYYY-MM-DDTHH-MMZ` (ví dụ: `2026-06-10T09-33Z`), hiển thị ngay dòng đầu của log xuất ra console hoặc ghi trong thư mục `artifacts/logs/`.

---

## 2. Cleaning & expectation

Tôi đã bổ sung các quy tắc làm sạch dữ liệu và bộ kiểm thử chất lượng nhằm lọc bỏ triệt để dữ liệu lỗi trước khi nạp vào vector database.

### 2a. Bảng metric_impact

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| `clean_noise_prefixes` (Rule) | 34 cleaned rows | 30 cleaned rows | Lọc bỏ 4 record chứa tiền tố nhiễu dạng `"Nội dung không rõ ràng: "` và `"!!!"` tránh trùng lặp mờ. |
| `chunk_text_too_short` (Rule) | 0 quarantined | 0 quarantined | Loại bỏ các record có text quá ngắn (< 15 ký tự). |
| `missing_exported_at` (Rule) | 0 quarantined | 0 quarantined | Yêu cầu bắt buộc trường `exported_at` để bảo đảm dòng thời gian dữ liệu. |
| `future_effective_date` (Rule) | 0 quarantined | 0 quarantined | Lọc bỏ các tài liệu có ngày hiệu lực ở tương lai so với ngày chạy batch. |
| `stale_policy_version` (Rule) | 0 quarantined | 47 quarantined | Lọc bỏ các tài liệu phiên bản cũ trước ngày `2026-01-01` (ngoại trừ SLA 2026). |
| `all_grading_sources_present` (Expectation) | N/A | OK (Pass) | Đảm bảo cả 5 nguồn dữ liệu phục vụ bộ câu hỏi đánh giá đều xuất hiện trong collection. |
| `no_duplicate_doc_text_pairs` (Expectation) | N/A | OK (Pass, 0 duplicates) | Kiểm tra dữ liệu sạch không chứa cặp `(doc_id, chunk_text)` trùng lặp. |

**Xử lý Expectation thất bại:**
Trong đợt chạy inject corruption (`--no-refund-fix`), expectation `refund_no_stale_14d_window` đã kích hoạt trạng thái **FAIL (halt)** do phát hiện 1 bản ghi chứa chu kỳ hoàn tiền 14 ngày làm việc. Pipeline lập tức dừng lại để bảo vệ cơ sở tri thức khỏi bị ô nhiễm thông tin sai lệch.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

- **Kịch bản Inject:** Chạy pipeline với cấu hình làm hỏng dữ liệu hoàn tiền bằng lệnh:
  ```bash
  .venv\Scripts\python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
  ```
- **Kết quả định lượng:**
  - File eval trước khi sửa (`after_inject_bad.csv`): Câu hỏi hoàn tiền `gq_d10_01` trả về kết quả chứa thông tin cũ `"14 ngày làm việc"` (`hits_forbidden = yes`).
  - File eval sau khi sửa (`after_fix_eval.csv`): Nhờ rule tự động sửa đổi và loại bỏ dữ liệu stale, câu truy vấn thu được chính xác kết quả `"7 ngày làm việc"` (`contains_expected = yes` và `hits_forbidden = no`), đồng thời các câu hỏi khác như IT Helpdesk Lockout, HR Leave Policy đều đạt tỷ lệ chính xác tuyệt đối.

---

## 4. Freshness & monitoring

- **SLA đã chọn:** 24 giờ kể từ thời điểm dữ liệu được xuất ra từ hệ thống nguồn (`latest_exported_at`).
- **Ý nghĩa các trạng thái:**
  - **PASS:** Dữ liệu mới cập nhật trong vòng 24 giờ.
  - **WARN:** Thiếu thông tin timestamp hợp lệ trong manifest nhưng pipeline vẫn chạy thành công.
  - **FAIL:** Dữ liệu đã quá 24 giờ (đối với tập dữ liệu mẫu ngày export là `2026-04-11` nên trạng thái báo `FAIL` là hoàn toàn chính xác).

---

## 5. Liên hệ Day 09

Dữ liệu sau khi làm sạch và embed thành công vào collection `day10_kb` sẽ được tích hợp làm nguồn tri thức (Knowledge Base) cho Multi-agent Day 09. Việc này đảm bảo Agent truy vấn chính xác thông tin mới nhất và không bị nhầm lẫn giữa các phiên bản chính sách cũ/mới (ví dụ: tư vấn đúng 12 ngày phép năm và 7 ngày hoàn tiền).

---

## 6. Rủi ro còn lại & việc chưa làm

- Cần xây dựng cơ chế tự động gửi thông báo khẩn cấp đến Slack/Teams khi freshness check báo `FAIL`.
- Nâng cấp bộ so khớp trùng lặp sử dụng MinHash để xử lý các tài liệu trùng lặp mờ thông minh hơn thay vì chỉ loại bỏ tiền tố thô sơ.
