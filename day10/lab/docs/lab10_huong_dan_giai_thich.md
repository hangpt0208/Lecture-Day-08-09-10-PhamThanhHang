# Hướng Dẫn Chi Tiết: Yêu Cầu Lab Day 10 & Giải Pháp Thực Hiện

Tài liệu này giải thích chi tiết các yêu cầu trong bài Lab Day 10 (Data Pipeline & Observability) và toàn bộ các phần việc tôi đã làm, các tệp tin đã sửa đổi và lý do đằng sau các quyết định kỹ thuật đó.

---

## 1. Phân Tích Yêu Cầu của `README.md`

Mục tiêu cốt lõi của Lab Day 10 là xây dựng một **Data Pipeline hoàn chỉnh** thực hiện 4 bước tự động: **Ingest (Thu nhận) -> Clean (Làm sạch) -> Validate (Kiểm tra chất lượng) -> Embed (Nhúng vector lưu vào ChromaDB)**. 

Dữ liệu đầu ra sau khi làm sạch phải đảm bảo hệ thống RAG (RAG Agent) trả lời đúng **tất cả 10 câu hỏi đánh giá** trong `data/grading_questions.json`.

Các yêu cầu cụ thể được chia theo 4 Sprint:
1. **Sprint 1 (Phân tích nguồn thô):** Chạy thử pipeline để xem lỗi dừng (halt), phân tích tệp `policy_export_dirty.csv` để phát hiện các nguồn dữ liệu bị bỏ sót hoặc bị cách ly (quarantine) nhầm.
2. **Sprint 2 (Làm sạch & Kiểm định):** Sửa các lỗi dữ liệu để pipeline chạy thành công (exit 0). Thêm tối thiểu **3 quy tắc làm sạch mới** và **2 bộ kiểm tra chất lượng (Expectations) mới**. Đảm bảo ghi nhận vào manifest và xử lý trùng lặp không phình tài nguyên (idempotency).
3. **Sprint 3 (Bằng chứng Trước/Sau):** Cố ý làm hỏng dữ liệu (inject corruption) để kiểm tra xem hệ thống RAG bị giảm chất lượng thế nào, sau đó khôi phục lại và đối chiếu độ chính xác. Lập báo cáo chất lượng (`quality_report`).
4. **Sprint 4 (Giám sát & Tài liệu):** Cài đặt cơ chế kiểm tra độ trễ dữ liệu (`freshness_check`), viết tài liệu vận hành (`runbook`), Data Contract, kiến trúc dữ liệu và báo cáo kết quả cá nhân.

---

## 2. Các File Đã Sửa Đổi & Nội Dung Chi Tiết

Dưới đây là danh sách các tệp tin tôi đã can thiệp chỉnh sửa để đáp ứng toàn bộ tiêu chí của bài Lab:

### A. Mã Nguồn Hệ Thống (Python)

#### 1. [transform/cleaning_rules.py](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/transform/cleaning_rules.py)
* **Vấn đề phát hiện:**
  - Nguồn dữ liệu cấp quyền truy cập hệ thống `access_control_sop` có xuất hiện trong dữ liệu thô và bộ câu hỏi đánh giá nhưng bị pipeline baseline gạt ra ngoài vì thiếu trong danh sách cho phép (`ALLOWED_DOC_IDS`).
  - Dữ liệu thô chứa nhiều bản ghi giống hệt nhau nhưng có thêm các tiền tố nhiễu ở đầu như `"Nội dung không rõ ràng: "` hoặc `"!!!"`. Cơ chế loại trùng lặp đơn giản của baseline bị bỏ sót do so khớp chuỗi khác nhau, làm nhiễu dữ liệu ChromaDB.
  - Trường `exported_at` bị lẫn định dạng sử dụng dấu gạch chéo `/` (ví dụ: `2026/04/11`) làm lỗi thư viện parse ngày tháng và làm sai thứ tự so sánh chuỗi ngày tháng.
* **Những gì đã sửa đổi:**
  - Thêm `"access_control_sop"` vào tập hợp `ALLOWED_DOC_IDS`.
  - Bổ sung vòng lặp tự động bóc tách và loại bỏ triệt để các tiền tố nhiễu ở đầu chuỗi văn bản (`chunk_text`) trước khi đưa vào các bước kiểm định và chống trùng lặp.
  - Chuẩn hóa trường `exported_at` bằng cách chuyển đổi `/` thành `-` để đồng nhất định dạng ISO.

#### 2. [etl_pipeline.py](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/etl_pipeline.py)
* **Vấn đề phát hiện:**
  - Khoảng cách từ vựng lớn giữa câu hỏi đánh giá (ví dụ: truy vấn về thời gian auto-escalation cho Ticket P1) và văn bản lưu trong database khiến model embedding (`all-MiniLM-L6-v2`) định vị sai mục tiêu, làm tài liệu cần tìm bị đẩy ra ngoài top 5 kết quả tìm kiếm (xếp hạng thứ 11).
  - Khi chạy trên Windows, tiến trình ghi log bị crash lỗi `UnicodeEncodeError cp1252` do in các ký tự mũi tên `→` và chữ tiếng Việt có dấu.
* **Những gì đã sửa đổi:**
  - Triển khai giải pháp **Context Prefixing**: Ánh xạ `doc_id` của từng tài liệu nguồn sang một tiền tố mô tả rõ nghĩa (ví dụ: `Cam kết chất lượng dịch vụ SLA P1 ticket P1 (sla p1 2026):` cho nguồn `sla_p1_2026`). Tiền tố này được ghép vào nội dung nhúng ngay trước khi đẩy vào ChromaDB, giúp tăng độ tương quan từ khóa một cách ngoạn mục mà không làm ảnh hưởng cấu trúc lưu trữ của tệp CSV sạch gốc.
  - Chuyển đổi toàn bộ các câu thông báo ghi log có chứa ký tự không thuộc bảng mã ASCII về dạng ký tự chuẩn để tương thích 100% với môi trường Windows Command Prompt/PowerShell.

---

### B. Cấu Hình & Hợp Đồng Dữ Liệu (YAML)

#### 3. [contracts/data_contract.yaml](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/contracts/data_contract.yaml)
* **Những gì đã sửa đổi:**
  - Điền các thông tin cam kết vận hành dữ liệu thực tế bao gồm `owner_team` là `"CS & IT Data Platform Team"` và kênh cảnh báo lỗi `alert_channel` là `"Slack #incident-p1"`.
  - Khai báo nguồn dữ liệu `access_control_sop` vào mục tài liệu canonical (`canonical_sources`) và danh sách ID được phép nạp (`allowed_doc_ids`) để đồng bộ với mã nguồn cleaning.

---

### C. Hồ Sơ Tài Liệu Vận Hành & Báo Cáo (Markdown)

#### 4. [docs/pipeline_architecture.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/docs/pipeline_architecture.md)
* Mô tả chi tiết kiến trúc của pipeline, tích hợp sơ đồ luồng dữ liệu tự động vẽ bằng **Merit/Mermaid**, ranh giới trách nhiệm, và làm rõ cơ chế kiểm soát trùng lặp vector (Idempotency - cơ chế prune vector cũ).

#### 5. [docs/data_contract.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/docs/data_contract.md)
* Mô tả chi tiết schema dữ liệu sạch đầu ra, cách ánh xạ 5 nguồn tài liệu gốc, và quy định chi tiết cách xử lý bản ghi lỗi (Quarantine) và bản ghi vô giá trị (Drop).

#### 6. [docs/runbook.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/docs/runbook.md)
* Thiết lập quy trình chẩn đoán sự cố dữ liệu theo cấu trúc chuẩn: **Symptom -> Detection -> Diagnosis -> Mitigation -> Prevention**, giúp người vận hành khắc phục nhanh khi Agent RAG trả lời sai lệch thông tin hoàn tiền hoặc ngày phép.

#### 7. [docs/quality_report.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/docs/quality_report.md)
* Báo cáo định lượng và đối chiếu số liệu record (raw: 247, clean: 30, quarantine: 217). Đính kèm so sánh kết quả truy vấn trước và sau khi sửa lỗi để chứng minh chất lượng RAG được khôi phục. Giải thích ý nghĩa của Freshness SLA.

#### 8. [reports/group_report.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/reports/group_report.md)
* Báo cáo tổng hợp tiến độ dự án (được tối ưu hóa cho bài nộp cá nhân của Phạm Thanh Hằng), thống kê bảng tác động định lượng (`metric_impact`) của các quy tắc làm sạch dữ liệu.

#### 9. [reports/individual/PhamThanhHang.md](file:///d:/PTH/Work/AI%20in%20Action/Exercise/B10/Lecture-Day-08-09-10-PhamThanhHang/day10/lab/reports/individual/PhamThanhHang.md)
* Báo cáo đóng góp cá nhân tự đánh giá vai trò phụ trách, giải thích cặn kẽ quyết định kỹ thuật về nhúng ngữ cảnh (Context Prefixing), cách xử lý các anomaly (lỗi dấu gạch chéo ngày tháng, lỗi encoder cp1252) và hướng cải tiến trong tương lai.

---

## 3. Kết Quả Kiểm Tra Độ Chính Xác

Sau khi áp dụng toàn bộ các giải pháp làm sạch dữ liệu và nhúng ngữ cảnh trên, tôi đã tiến hành kiểm tra bằng bộ công cụ đánh giá chính thức:
* Khi chạy `grading_run.py`, toàn bộ **10 câu hỏi đều vượt qua thành công** (`contains_expected: true` và không có câu nào bị dính từ khóa cấm `hits_forbidden`).
* Khi chạy công cụ kiểm định nhanh `instructor_quick_check.py` của giảng viên cho cả manifest và grading file, tất cả các tiêu chí đều đạt trạng thái **OK / PASS**.
