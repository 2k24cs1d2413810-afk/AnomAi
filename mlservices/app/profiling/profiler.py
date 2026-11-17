import numpy as np
import pandas as pd

from app.profiling.semantic_classifier import classify_column


INTERNAL_COLUMNS = {
    "_anomai_source_row"
}


def _sample_values(series, limit=5):
    values = []

    for value in series.dropna().head(limit):

        if isinstance(value, np.generic):
            value = value.item()

        values.append(value)

    return values


def _numeric_statistics(series):
    numeric_series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if numeric_series.empty:
        return {}

    return {
        "count": int(
            numeric_series.count()
        ),
        "min": float(
            numeric_series.min()
        ),
        "max": float(
            numeric_series.max()
        ),
        "mean": float(
            numeric_series.mean()
        ),
        "median": float(
            numeric_series.median()
        ),
        "std": (
            float(numeric_series.std())
            if len(numeric_series) > 1
            else 0.0
        )
    }


def profile_dataset(df):
    """
    Generate a descriptive profile of the uploaded dataset.

    Internal AnomAI columns are excluded from the user-facing
    profile.
    """

    data_columns = [
        column
        for column in df.columns
        if column not in INTERNAL_COLUMNS
    ]

    total_rows = len(df)
    total_columns = len(data_columns)

    duplicate_rows = int(
        df[data_columns].duplicated().sum()
    )

    memory_usage = int(
        df[data_columns]
        .memory_usage(
            deep=True
        )
        .sum()
    )

    columns = []

    for column in data_columns:

        series = df[column]

        missing_count = int(
            series.isna().sum()
        )

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        is_numeric = pd.api.types.is_numeric_dtype(
            series
        )

        is_datetime = pd.api.types.is_datetime64_any_dtype(
            series
        )

        column_profile = {
            "name": column,
            "semantic_role": classify_column(column),
            "data_type": str(
                series.dtype
            ),
            "missing_count": missing_count,
            "missing_percentage": round(
                (
                    missing_count
                    / total_rows
                    * 100
                )
                if total_rows
                else 0,
                2
            ),
            "unique_count": unique_count,
            "unique_percentage": round(
                (
                    unique_count
                    / total_rows
                    * 100
                )
                if total_rows
                else 0,
                2
            ),
            "is_numeric": bool(
                is_numeric
            ),
            "is_datetime": bool(
                is_datetime
            ),
            "sample_values": _sample_values(
                series
            )
        }

        if is_numeric:
            column_profile["statistics"] = (
                _numeric_statistics(series)
            )
        else:
            column_profile["statistics"] = {}

        columns.append(
            column_profile
        )

    return {
        "dataset": {
            "rows": total_rows,
            "columns": total_columns,
            "duplicate_rows": duplicate_rows,
            "memory_usage_bytes": memory_usage
        },
        "columns": columns
    }