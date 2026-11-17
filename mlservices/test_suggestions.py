from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.anomaly_engine import analyze_anomalies
from app.remidiation.suggestions import generate_suggestions


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

analysis = analyze_anomalies(
    df,
    statistical_method="iqr",
    contamination=0.25
)

suggestions = generate_suggestions(
    df,
    analysis["issues"]
)

print("\n========== SUGGESTIONS ==========\n")

pprint(suggestions)