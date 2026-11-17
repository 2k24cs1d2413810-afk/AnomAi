from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.anomaly_engine import analyze_anomalies


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

result = analyze_anomalies(
    df,
    statistical_method="iqr",
    contamination=0.25
)

print("\n========== SUMMARY ==========\n")

pprint(result["summary"])

print("\n========== ISSUES ==========\n")

pprint(result["issues"])