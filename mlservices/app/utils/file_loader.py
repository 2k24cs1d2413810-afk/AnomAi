import json
import os

import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv", ".tsv", ".txt", ".xlsx", ".xls", ".ods",
    ".json", ".jsonl", ".ndjson", ".xml", ".parquet"
}

SOURCE_ROW_COLUMN = "_anomai_source_row"


def _read_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if isinstance(payload, dict):
        # Support {"data": [...]} and ordinary column-oriented JSON.
        if isinstance(payload.get("data"), list):
            return pd.DataFrame(payload["data"])
        return pd.DataFrame(payload)
    raise ValueError("JSON must contain an array or an object representing tabular data.")


def load_dataset(file_path):
    if not file_path:
        raise ValueError("No file path was provided.")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"The provided path is not a file: {file_path}")

    extension = os.path.splitext(file_path)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file format. Supported formats are CSV, TSV, TXT, XLSX, XLS, ODS, JSON, JSONL, NDJSON, XML and Parquet."
        )

    try:
        if extension == ".csv":
            df = pd.read_csv(file_path)
        elif extension in {".tsv", ".txt"}:
            df = pd.read_csv(file_path, sep="\t")
        elif extension in {".xlsx", ".xls", ".ods"}:
            df = pd.read_excel(file_path)
        elif extension == ".parquet":
            df = pd.read_parquet(file_path)
        elif extension == ".xml":
            df = pd.read_xml(file_path)
        elif extension == ".json":
            df = _read_json(file_path)
        else:
            df = pd.read_json(file_path, lines=True)
    except Exception as error:
        raise ValueError(f"Unable to read dataset: {error}") from error

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("The dataset is empty or does not contain tabular records.")

    if SOURCE_ROW_COLUMN in df.columns:
        raise ValueError(f"The column name '{SOURCE_ROW_COLUMN}' is reserved by AnomAI.")

    # Make duplicate column names deterministic before profiling.
    if df.columns.duplicated().any():
        duplicates = list(df.columns[df.columns.duplicated()])
        raise ValueError(f"Duplicate column names are not allowed: {duplicates}")

    df.insert(0, SOURCE_ROW_COLUMN, range(2, len(df) + 2))
    return df
