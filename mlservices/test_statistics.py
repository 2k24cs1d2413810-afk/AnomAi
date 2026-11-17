from pprint import pprint

from app.utils.file_loader import load_dataset
from app.profiling.statistics import analyze_statistics


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

statistics = analyze_statistics(df)

pprint(statistics)