from pprint import pprint

from app.utils.file_loader import load_dataset
from app.profiling.profiler import profile_dataset


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

profile = profile_dataset(df)

pprint(profile)