import json
from transform.cleaning_rules import ALLOWED_DOC_IDS

# ==================================================
# Load grading questions
# ==================================================
with open("data/grading_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# ==================================================
# Lấy tất cả expect_top1_doc_id
# ==================================================
expected_doc_ids = set()

for q in questions:
    doc_id = q.get("expect_top1_doc_id")

    if doc_id:
        expected_doc_ids.add(doc_id)

print("=" * 60)
print("DOC_ID ĐƯỢC YÊUU CẦU TRONG BỘ ĐÁNH GIÁ")
print("=" * 60)

for doc_id in sorted(expected_doc_ids):
    print(doc_id)

print(f"\nTổng số nguồn cần có: {len(expected_doc_ids)}")

# ==================================================
# So sánh với ALLOWED_DOC_IDS
# ==================================================
allowed_doc_ids = set(ALLOWED_DOC_IDS)

missing = expected_doc_ids - allowed_doc_ids

print("\n" + "=" * 60)
print("NGUỒN CẦN CHO ĐÁNH GIÁ NHƯNG KHÔNG ĐƯỢC PIPELINE CHO PHÉP")
print("=" * 60)

if missing:
    for doc_id in sorted(missing):
        print(doc_id)
else:
    print("Không thiếu nguồn nào.")

# ==================================================
# Các nguồn được allow nhưng không dùng trong grading
# ==================================================
extra = allowed_doc_ids - expected_doc_ids

print("\n" + "=" * 60)
print("NGUỒN ĐƯỢC ALLOW NHƯNG KHÔNG XUẤT HIỆN TRONG GRADING")
print("=" * 60)

for doc_id in sorted(extra):
    print(doc_id)