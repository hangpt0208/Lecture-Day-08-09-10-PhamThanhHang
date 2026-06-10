# Runbook — Lab Day 10 (Sự cố dữ liệu và khôi phục)

Tài liệu hướng dẫn chẩn đoán và khắc phục nhanh khi hệ thống RAG phục vụ thông tin sai lệch hoặc dữ liệu bị trễ hạn (stale).

---

## Symptom (Triệu chứng)

- **Sai lệch nội dung câu trả lời:** Người dùng hoặc Agent trả lời sai chính sách hoàn tiền là "14 ngày làm việc" thay vì "7 ngày làm việc".
- **Sai lệch chính sách nghỉ phép:** Hệ thống tư vấn nhân viên dưới 3 năm kinh nghiệm được "10 ngày phép năm" (thay vì "12 ngày" theo chính sách 2026).
- **Thiếu thông tin tra cứu:** Agent không thể trả lời câu hỏi liên quan đến cấp quyền truy cập quản trị hệ thống (`access_control_sop`).

---

## Detection (Phát hiện)

- **Halt Pipeline:** Tiến trình ETL bị dừng đột ngột tại bước kiểm tra chất lượng dữ liệu với mã exit code = 2.
- **Freshness SLA Fail:** Hệ thống giám sát ghi nhận log `freshness_check=FAIL` kèm cảnh báo `"reason": "freshness_sla_exceeded"`.
- **Đánh giá tự động thất bại:** Kiểm tra định kỳ bằng `eval_retrieval.py` báo cáo cột `hits_forbidden` hoặc `contains_expected` có giá trị bất thường.

---

## Diagnosis (Chẩn đoán)

| Bước | Việc làm | Kết quả mong đợi / Hướng xử lý |
|------|----------|------------------|
| 1 | Kiểm tra file manifest chạy gần nhất trong `artifacts/manifests/manifest_<run-id>.json` | Xác định `latest_exported_at` có bị cũ hơn 24 giờ so với hiện tại không. Kiểm tra cờ `skipped_validate`. |
| 2 | Mở file quarantine `artifacts/quarantine/quarantine_<run-id>.csv` | Lọc theo cột `reason` để tìm nguyên nhân bản ghi bị cách ly (ví dụ: `stale_hr_policy_content`, `future_effective_date`). |
| 3 | Chạy thử nghiệm tự kiểm tra thu hồi thông tin | Thực hiện lệnh: <br> `python eval_retrieval.py --out artifacts/eval/after_fix_eval.csv` <br> Xem file CSV để kiểm tra độ chính xác của các câu truy vấn thực tế. |

---

## Mitigation (Khắc phục tạm thời)

1. **Khôi phục dữ liệu chuẩn:** Chạy lại pipeline ETL với cấu hình đầy đủ để làm sạch và cập nhật lại vector store:
   ```bash
   .venv\Scripts\python etl_pipeline.py run
   ```
2. **Loại bỏ dữ liệu lỗi (Pruning):** Đảm bảo cơ chế prune của pipeline hoạt động bằng cách kiểm tra log `embed_prune_removed` lớn hơn 0 để chắc chắn các vector bị lỗi/cũ đã bị xóa khỏi ChromaDB.
3. **Cập nhật thời gian xuất:** Nếu hệ thống nguồn trễ hạn xuất file export nhưng dữ liệu bên trong vẫn đúng, có thể cập nhật cấu hình `FRESHNESS_SLA_HOURS` hoặc xin phê duyệt bỏ qua SLA tạm thời từ Data Owner.

---

## Prevention (Phòng ngừa dài hạn)

- **Đồng bộ Data Contract:** Thêm các ràng buộc mới vào `contracts/data_contract.yaml` để kiểm soát dữ liệu ngay từ đầu nguồn.
- **Giám sát Freshness ở 2 đầu:** Cấu hình hệ thống tự động chạy `python etl_pipeline.py freshness --manifest ...` định kỳ 1 giờ/lần để phát hiện chậm trễ đồng bộ.
- **Không hard-code tham số:** Đưa các mốc ngày hiệu lực (cutoff dates) của các chính sách vào tệp cấu hình thay vì viết cứng trong mã nguồn python.
