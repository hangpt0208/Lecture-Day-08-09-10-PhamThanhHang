import pandas as pd
from transform.cleaning_rules import ALLOWED_DOC_IDS

# Đọc dữ liệu raw
csv_path = "data/raw/policy_export_dirty.csv"
df = pd.read_csv(csv_path)

# ==================================================
# 1. Phân tích doc_id trong CSV
# ==================================================
raw_doc_ids = set(df["doc_id"].dropna().unique())

print("=" * 60)
print("DOC_ID TRONG CSV")
print("=" * 60)

print(f"Số doc_id unique: {len(raw_doc_ids)}")
print()

for doc_id in sorted(raw_doc_ids):
    count = (df["doc_id"] == doc_id).sum()
    print(f"{doc_id:<30} {count:>5} records")

# ==================================================
# 2. ALLOWED_DOC_IDS
# ==================================================
allowed_doc_ids = set(ALLOWED_DOC_IDS)

print("\n" + "=" * 60)
print("ALLOWED_DOC_IDS")
print("=" * 60)

print(f"Số doc_id được phép: {len(allowed_doc_ids)}")
print()

for doc_id in sorted(allowed_doc_ids):
    print(doc_id)

# ==================================================
# 3. Tìm doc_id có thể bị quarantine nhầm
# ==================================================
unexpected_ids = raw_doc_ids - allowed_doc_ids

print("\n" + "=" * 60)
print("DOC_ID XUẤT HIỆN TRONG CSV NHƯNG KHÔNG ĐƯỢC ALLOW")
print("=" * 60)

if unexpected_ids:
    for doc_id in sorted(unexpected_ids):
        count = (df["doc_id"] == doc_id).sum()
        print(f"{doc_id:<30} {count:>5} records")
else:
    print("Không có.")

# ==================================================
# 4. Chi tiết các dòng có thể bị quarantine
# ==================================================
if unexpected_ids:
    print("\n" + "=" * 60)
    print("CHI TIẾT CÁC DÒNG CÓ THỂ BỊ QUARANTINE")
    print("=" * 60)

    suspicious_rows = df[df["doc_id"].isin(unexpected_ids)]

    cols = [
        "chunk_id",
        "doc_id",
        "effective_date",
        "exported_at"
    ]

    print(suspicious_rows[cols].to_string(index=False))