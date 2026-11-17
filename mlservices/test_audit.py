from app.utils.file_loader import load_dataset
from app.anomaly.anomaly_engine import analyze_anomalies
from app.remidiation.cleaner import clean_dataset
from app.remidiation.audit import create_audit_trail


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

analysis = analyze_anomalies(
    df,
    statistical_method="iqr",
    contamination=0.25
)

cleaned_df, changes = clean_dataset(
    df,
    analysis["issues"]
)

audit_records = create_audit_trail(changes)


print("\n========== REMEDIATION CHANGES ==========")

for change in changes:
    print(change)


print("\n========== AUDIT TRAIL ==========")

for record in audit_records:
    print(record)