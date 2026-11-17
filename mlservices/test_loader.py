from app.utils.file_loader import load_dataset


file_path = "datasets/test_dataset.csv"

df = load_dataset(file_path)

print("Dataset loaded successfully!")
print()

print("Rows:", len(df))
print("Columns:", len(df.columns))
print()

print(df)