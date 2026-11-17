from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.anomaly_engine import analyze_anomalies
from app.scoring.quality_score import calculate_quality_score


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

analysis = analyze_anomalies(
    df,
    statistical_method="iqr",
    contamination=0.25
)

quality = calculate_quality_score(
    df,
    analysis["issues"]
)

print("\n========== QUALITY SCORE ==========\n")

pprint(quality)