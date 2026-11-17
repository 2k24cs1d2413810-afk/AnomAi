import pandas as pd

from app.profiling.semantic_classifier import classify_column

SOURCE_ROW_COLUMN = "_anomai_source_row"


def _safe_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass
    return value


def _record_change(changes, row_index, source_row, column, old_value, new_value, reason, action="update_value", automatic=True):
    changes.append({
        "action": action,
        "row_index": int(row_index) if row_index is not None else None,
        "source_row": int(source_row) if source_row is not None else None,
        "column": column,
        "old_value": _safe_value(old_value),
        "new_value": _safe_value(new_value),
        "reason": reason,
        "automatic": automatic
    })


def _source_row(df, index):
    return df.at[index, SOURCE_ROW_COLUMN] if SOURCE_ROW_COLUMN in df.columns else None


def _clean_whitespace(df, changes):
    for column in df.select_dtypes(include=["object", "string"]).columns:
        if column == SOURCE_ROW_COLUMN:
            continue
        for index in df.index:
            value = df.at[index, column]
            if pd.isna(value) or not isinstance(value, str):
                continue
            cleaned = value.strip()
            if cleaned != value:
                df.at[index, column] = cleaned
                _record_change(changes, index, _source_row(df, index), column, value, cleaned,
                               "Removed leading and trailing whitespace.")


def _normalize_emails(df, changes):
    for column in df.columns:
        if column == SOURCE_ROW_COLUMN or classify_column(column) != "email":
            continue
        for index in df.index:
            value = df.at[index, column]
            if pd.isna(value) or not isinstance(value, str):
                continue
            normalized = value.strip().lower()
            if normalized != value:
                df.at[index, column] = normalized
                _record_change(changes, index, _source_row(df, index), column, value, normalized,
                               "Normalized email formatting by trimming whitespace and converting to lowercase.")


def _remove_exact_duplicates(df, changes):
    data_columns = [c for c in df.columns if c != SOURCE_ROW_COLUMN]
    mask = df[data_columns].duplicated(keep="first")
    duplicate_indices = df.index[mask].tolist()
    for index in duplicate_indices:
        changes.append({
            "action": "remove_duplicate_row",
            "row_index": int(index),
            "source_row": int(_source_row(df, index)) if _source_row(df, index) is not None else None,
            "column": None,
            "old_value": None,
            "new_value": None,
            "reason": "Exact duplicate row detected; later occurrence removed while preserving the first occurrence.",
            "automatic": True
        })
    return df.drop(index=duplicate_indices).reset_index(drop=True)


def _fill_missing_numeric(df, changes):
    for column in df.columns:
        if column == SOURCE_ROW_COLUMN or not pd.api.types.is_numeric_dtype(df[column]):
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()
        if valid.empty:
            continue
        median = valid.median()
        for index in df.index[series.isna()]:
            df.at[index, column] = median
            _record_change(changes, index, _source_row(df, index), column, None, median,
                           "Missing numeric value replaced with the column median calculated from available values.")


def _repair_invalid_age(df, changes):
    for column in df.columns:
        if column == SOURCE_ROW_COLUMN or classify_column(column) != "age":
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        valid = numeric[(numeric >= 0) & (numeric <= 120)]
        if valid.empty:
            continue
        median = valid.median()
        if not pd.api.types.is_float_dtype(df[column]):
            df[column] = pd.to_numeric(df[column], errors="coerce").astype(float)
        for index in df.index:
            value = numeric.loc[index]
            if pd.isna(value) or 0 <= value <= 120:
                continue
            old = df.at[index, column]
            df.at[index, column] = median
            _record_change(changes, index, _source_row(df, index), column, old, median,
                           "Invalid age replaced with the median of values within a valid 0-120 age range.")


def _replace_numeric_outliers(df, changes):
    for column in df.select_dtypes(include="number").columns:
        if column == SOURCE_ROW_COLUMN:
            continue
        role = classify_column(column)
        if role == "identifier":
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        valid = numeric.dropna()
        if len(valid) < 8:
            continue
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        inliers = valid[(valid >= lower) & (valid <= upper)]
        if inliers.empty:
            continue
        replacement = inliers.median()
        if not pd.api.types.is_float_dtype(df[column]):
            df[column] = pd.to_numeric(df[column], errors="coerce").astype(float)
        for index in df.index:
            value = numeric.loc[index]
            if pd.isna(value) or lower <= value <= upper:
                continue
            # Do not overwrite a clearly invalid financial sign; that needs review.
            if role == "financial" and value < 0:
                continue
            old = df.at[index, column]
            df.at[index, column] = replacement
            _record_change(changes, index, _source_row(df, index), column, old, replacement,
                           f"Statistical outlier replaced with the median of non-outlier {column} values using the IQR rule.")


def clean_dataset(df, findings):
    cleaned_df = df.copy(deep=True)
    changes = []
    _clean_whitespace(cleaned_df, changes)
    _normalize_emails(cleaned_df, changes)
    cleaned_df = _remove_exact_duplicates(cleaned_df, changes)
    _fill_missing_numeric(cleaned_df, changes)
    _repair_invalid_age(cleaned_df, changes)
    _replace_numeric_outliers(cleaned_df, changes)
    return cleaned_df, changes
