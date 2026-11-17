import numpy as np
import pandas as pd


INTERNAL_COLUMNS = {
    "_anomai_source_row"
}


def analyze_statistics(df):
    """
    Analyze statistical properties of numeric user-data columns.

    Internal AnomAI provenance columns are excluded.
    """

    numeric_columns = [
        column
        for column in df.select_dtypes(
            include=np.number
        ).columns
        if column not in INTERNAL_COLUMNS
    ]

    results = {}

    for column in numeric_columns:

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q2 = series.quantile(0.50)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (
            1.5 * iqr
        )

        upper_bound = q3 + (
            1.5 * iqr
        )

        results[column] = {
            "count": int(
                series.count()
            ),
            "min": float(
                series.min()
            ),
            "max": float(
                series.max()
            ),
            "mean": float(
                series.mean()
            ),
            "median": float(
                series.median()
            ),
            "variance": float(
                series.var()
            ) if len(series) > 1 else 0.0,
            "std": float(
                series.std()
            ) if len(series) > 1 else 0.0,
            "q1": float(q1),
            "q2": float(q2),
            "q3": float(q3),
            "iqr": float(iqr),
            "skewness": (
                float(series.skew())
                if len(series) > 2
                else 0.0
            ),
            "zero_count": int(
                (series == 0).sum()
            ),
            "zero_percentage": round(
                (
                    (series == 0).sum()
                    / len(series)
                    * 100
                ),
                2
            ),
            "iqr_bounds": {
                "lower": float(
                    lower_bound
                ),
                "upper": float(
                    upper_bound
                )
            }
        }

    return results