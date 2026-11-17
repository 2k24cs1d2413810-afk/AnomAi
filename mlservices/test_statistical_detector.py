from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.statistical_detector import (
    detect_statistical_anomalies
)


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

anomalies = detect_statistical_anomalies(
    df,
    method="iqr"
)

print(
    f"Total statistical anomalies: {len(anomalies)}"
)

pprint(anomalies)