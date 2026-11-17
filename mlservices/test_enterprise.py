from app.pipeline import run_pipeline


result = run_pipeline(
    "datasets/anomai_enterprise_test.csv",
    statistical_method="iqr",
    contamination=0.05
)


print("\n" + "=" * 70)
print("             ANOMAI ENTERPRISE ML TEST")
print("=" * 70)

print("\n--- DATASET ---")
print("Original rows:", result["dataset"]["original_rows"])
print("Cleaned rows:", result["dataset"]["cleaned_rows"])
print("Original columns:", result["dataset"]["original_columns"])
print("Cleaned columns:", result["dataset"]["cleaned_columns"])

print("\n--- ML ANALYSIS ---")

ml = result["anomalies"]["before"]["ml_analysis"]

print("Status:", ml["status"])
print("Reason:", ml["reason"])
print("Model:", ml["model"])
print("Actual rows:", ml["actual_rows"])
print("Minimum rows:", ml["minimum_rows"])
print("Contamination:", ml["contamination"])

print("Features used:", ml["features_used"])
print("Features skipped:", ml["features_skipped"])

print("\n--- ANOMALY SUMMARY ---")

summary = result["anomalies"]["before"]["summary"]

for key, value in summary.items():
    print(f"{key}: {value}")

print("\n--- ML EVIDENCE ---")

for issue in result["anomalies"]["before"]["evidence"]:
    if issue.get("detection_method") == "isolation_forest":
        print(issue)

print("\n--- ALL FINDINGS ---")

for finding in result["anomalies"]["before"]["findings"]:
    print(
        f"source_row={finding['source_row']} | "
        f"column={finding['column']} | "
        f"type={finding['issue_type']} | "
        f"severity={finding['severity']} | "
        f"confidence={finding['confidence']} | "
        f"methods={finding['detection_methods']}"
    )

print("\n--- REMIDIATION CHANGES ---")

for change in result["remidiation"]["changes"]:
    print(change)

print("\n" + "=" * 70)
print("                 TEST COMPLETE")
print("=" * 70)