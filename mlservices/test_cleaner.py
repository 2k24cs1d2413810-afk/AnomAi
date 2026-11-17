from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.anomaly_engine import analyze_anomalies
from app.remidiation.cleaner import clean_dataset


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

print("\n========== ORIGINAL DATA ==========\n")

print(df)

print("\n========== CLEANED DATA ==========\n")

print(cleaned_df)

print("\n========== CHANGES ==========\n")

pprint(changes)