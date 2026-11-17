from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.ml_detector import detect_ml_anomalies


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

anomalies = detect_ml_anomalies(
    df,
    contamination=0.25
)

print(
    f"Total ML anomalies: {len(anomalies)}"
)

pprint(anomalies)