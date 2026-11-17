from pprint import pprint

from app.utils.file_loader import load_dataset
from app.anomaly.rule_detector import detect_rule_violations


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

issues = detect_rule_violations(df)

print(f"Total rule violations: {len(issues)}")

pprint(issues)