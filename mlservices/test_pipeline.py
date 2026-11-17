
from app.pipeline import run_pipeline


# --------------------------------------------------
# DATASET PATH
# --------------------------------------------------

file_path = "datasets/remidiation_test.csv"


# --------------------------------------------------
# RUN ANOMAI PIPELINE
# --------------------------------------------------

result = run_pipeline(
    file_path=file_path,
    statistical_method="iqr",
    contamination=0.25
)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\n")
print("=" * 60)
print("                ANOMAI PIPELINE RESULT")
print("=" * 60)


# --------------------------------------------------
# DATASET INFORMATION
# --------------------------------------------------

print("\n--- DATASET INFORMATION ---")

print(
    "Original rows:",
    result["dataset"]["original_rows"]
)

print(
    "Original columns:",
    result["dataset"]["original_columns"]
)

print(
    "Cleaned rows:",
    result["dataset"]["cleaned_rows"]
)

print(
    "Cleaned columns:",
    result["dataset"]["cleaned_columns"]
)


# --------------------------------------------------
# QUALITY SCORE
# --------------------------------------------------

print("\n--- QUALITY SCORE BEFORE CLEANING ---")

print(result["quality"]["before"])


print("\n--- QUALITY SCORE AFTER CLEANING ---")

print(result["quality"]["after"])


# --------------------------------------------------
# ANOMALY SUMMARY BEFORE CLEANING
# --------------------------------------------------

print("\n--- ANOMALY SUMMARY BEFORE CLEANING ---")

print(
    result["anomalies"]["before"]["summary"]
)


# --------------------------------------------------
# ANOMALY SUMMARY AFTER CLEANING
# --------------------------------------------------

print("\n--- ANOMALY SUMMARY AFTER CLEANING ---")

print(
    result["anomalies"]["after"]["summary"]
)


# --------------------------------------------------
# REMIDIATION CHANGES
# --------------------------------------------------

print("\n--- REMIDIATION CHANGES ---")

changes = result["remidiation"]["changes"]

if not changes:
    print("No automatic changes were made.")

else:
    for change in changes:
        print(change)


# --------------------------------------------------
# AUDIT TRAIL
# --------------------------------------------------

print("\n--- AUDIT TRAIL ---")

audit_records = result["remidiation"]["audit"]

if not audit_records:
    print("No audit records available.")

else:
    for record in audit_records:
        print(record)


# --------------------------------------------------
# REMIDIATION SUGGESTIONS
# --------------------------------------------------

print("\n--- REMIDIATION SUGGESTIONS ---")

suggestions = result["remidiation"]["suggestions"]

if not suggestions:
    print("No remediation suggestions generated.")

else:
    for suggestion in suggestions:
        print(suggestion)


# --------------------------------------------------
# CLEANED DATASET
# --------------------------------------------------

print("\n--- CLEANED DATASET ---")

print(
    result["cleaned_data"].to_string(index=False)
)


print("\n")
print("=" * 60)
print("             PIPELINE EXECUTION COMPLETE")
print("=" * 60)
