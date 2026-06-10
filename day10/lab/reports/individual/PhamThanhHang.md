# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phạm Thanh Hằng  
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring (Tự thực hiện toàn bộ)  
**Ngày nộp:** 2026-06-10  

---

## 1. Tôi phụ trách phần nào?

**File / module:**
- Sửa đổi [cleaning_rules.py](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/transform/cleaning_rules.py): Thêm logic làm sạch tiền tố nhiễu (`"Nội dung không rõ ràng: "` và `"!!!"`) và chuẩn hóa dấu gạch chéo trong `exported_at`.
- Sửa đổi [etl_pipeline.py](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/etl_pipeline.py): Tích hợp giải pháp Context Prefixing khi embed dữ liệu để cải thiện độ chính xác tìm kiếm của ChromaDB, sửa các lỗi Encode cp1252 trên Windows.

**Bằng chứng:**
- Hàm `clean_rows` trong `transform/cleaning_rules.py` có vòng lặp strip nhiễu tiền tố và `replace("/", "-")` cho `exported_at`.
- Khối code `CONTEXT_MAP` ánh xạ và tiền tố hóa văn bản trước khi gọi `col.upsert` trong hàm `cmd_embed_internal` của `etl_pipeline.py`.

---

## 2. Một quyết định kỹ thuật

**Quyết định Context Prefixing khi Embed:**
Tôi chọn giữ nguyên nội dung gốc sạch trong file CSV (`cleaned_*.csv`) để duy trì đúng cấu trúc dữ liệu theo Hợp đồng dữ liệu (Data Contract). Tuy nhiên, trong bước nhúng vector (`cmd_embed_internal`), tôi đã tạo một ánh xạ ngữ cảnh `CONTEXT_MAP` nhằm bổ sung tiền tố tài liệu (ví dụ: `Cam kết chất lượng dịch vụ SLA P1 ticket P1...` cho doc `sla_p1_2026`). 

Điều này giúp cầu nối khoảng cách ngữ nghĩa giữa các câu hỏi truy vấn của người dùng (thường chứa các từ khóa như "ticket P1", "hệ thống", "hoàn tiền") và các câu ngắn trong tài liệu gốc. Quyết định này giúp khắc phục hoàn toàn hiện tượng tài liệu đúng bị đẩy xuống dưới top-5 và giúp đạt điểm 10/10 trong bộ câu hỏi đánh giá.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Anomaly 1: Freshness Check trả về WARN**
- *Triệu chứng:* Log giám sát hiển thị `freshness_check=WARN {"reason": "no_timestamp_in_manifest"}` mặc dù file manifest ghi nhận đầy đủ thông tin.
- *Phát hiện:* Hàm `parse_iso` thất bại khi phân tích `"2026/04/11T00:00:00"` do có dấu gạch chéo `/` thay vì dấu gạch ngang `-`. Điều này cũng làm hàm `max()` so sánh chuỗi bị lệch (dấu `/` lớn hơn dấu `-` trong bảng ASCII).
- *Khắc phục:* Tôi thêm `.replace("/", "-")` cho `exported_at` trong hàm `clean_rows`. Sau khi sửa, timestamp được parse thành công, và hệ thống cảnh báo đúng trạng thái `FAIL` do dữ liệu mẫu quá thời hạn 24 giờ.

**Anomaly 2: Lỗi Encoder cp1252 trên Windows console**
- *Triệu chứng:* Pipeline crash đột ngột với lỗi `UnicodeEncodeError: 'charmap' codec can't encode...` khi in ra log chứa ký tự mũi tên `→` và chữ tiếng Việt có dấu.
- *Khắc phục:* Tôi đã chuẩn hóa các chuỗi thông báo log trong `etl_pipeline.py` về dạng ký tự chuẩn ASCII (ví dụ thay `→` bằng `->`), đảm bảo pipeline chạy thông suốt trên hệ điều hành Windows.

---

## 4. Bằng chứng trước / sau

- **Run ID chạy chuẩn:** `2026-06-10T09-33Z`
- **Trước cải tiến (`after_inject_bad.csv`):**
  `gq_d10_01,Theo chính sách hoàn tiền hiện hành...,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày...,no,yes,yes,3`
- **Sau cải tiến (`after_fix_eval.csv`):**
  `gq_d10_01,Theo chính sách hoàn tiền hiện hành...,policy_refund_v4,Chính sách hoàn tiền (policy refund v4): Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày...,yes,no,yes,3`

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ tích hợp thư viện **Great Expectations** (GE) thực tế thay vì dùng suite tự chế. Cụ thể là khởi tạo một `DataContext` và định nghĩa các checkpoint để kiểm tra schema, kiểu dữ liệu, định dạng ngày tháng của file CSV đã làm sạch trước khi nạp vào vector store, giúp pipeline có tính mở rộng cao và chuyên nghiệp hơn.
