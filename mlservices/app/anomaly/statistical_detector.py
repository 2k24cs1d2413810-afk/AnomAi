import numpy as np
import pandas as pd


INTERNAL_COLUMNS = {
    "_anomai_source_row"
}


def _calculate_confidence(distance_ratio):

    if distance_ratio <= 0:
        return 0.50

    confidence = (
        0.50
        + (
            1
            - np.exp(
                -distance_ratio
            )
        )
    )

    return round(
        min(confidence, 0.99),
        2
    )


def _calculate_severity(distance_ratio):

    if distance_ratio >= 3:
        return "high"

    if distance_ratio >= 1.5:
        return "medium"

    return "low"


def detect_statistical_anomalies(
    df,
    method="iqr",
    min_samples=8
):

    issues = []

    numeric_columns = [
        column
        for column in df.select_dtypes(
            include=np.number
        ).columns
        if column not in INTERNAL_COLUMNS
    ]

    for column in numeric_columns:

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        sample_count = len(series)

        if sample_count < min_samples:
            continue

        if method == "iqr":

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)

            iqr = q3 - q1

            lower_bound = (
                q1 - 1.5 * iqr
            )

            upper_bound = (
                q3 + 1.5 * iqr
            )

            for index, value in df[column].items():

                if pd.isna(value):
                    continue

                numeric_value = float(
                    value
                )

                if (
                    numeric_value >= lower_bound
                    and numeric_value <= upper_bound
                ):
                    continue

                if numeric_value < lower_bound:
                    distance = (
                        lower_bound
                        - numeric_value
                    )
                else:
                    distance = (
                        numeric_value
                        - upper_bound
                    )

                scale = max(
                    float(iqr),
                    1e-9
                )

                distance_ratio = (
                    distance / scale
                )

                confidence = (
                    _calculate_confidence(
                        distance_ratio
                    )
                )

                severity = (
                    _calculate_severity(
                        distance_ratio
                    )
                )

                source_row = df.at[
                    index,
                    "_anomai_source_row"
                ] if "_anomai_source_row" in df.columns else (
                    int(index) + 2
                )

                issues.append({
                    "row_index": int(index),
                    "source_row": int(source_row),
                    "column": column,
                    "value": value,
                    "issue_type": "statistical_outlier",
                    "detection_method": "iqr",
                    "severity": severity,
                    "confidence": confidence,
                    "sample_size": sample_count,
                    "expected_range": {
                        "lower": round(
                            float(lower_bound),
                            4
                        ),
                        "upper": round(
                            float(upper_bound),
                            4
                        )
                    },
                    "distance_from_boundary": round(
                        float(distance),
                        4
                    ),
                    "distance_ratio": round(
                        float(distance_ratio),
                        4
                    ),
                    "message": (
                        f"Value {value} in column "
                        f"'{column}' is outside the "
                        f"expected statistical range."
                    )
                })

        elif method == "zscore":

            mean = series.mean()
            std = series.std()

            if std == 0 or pd.isna(std):
                continue

            for index, value in df[column].items():

                if pd.isna(value):
                    continue

                numeric_value = float(
                    value
                )

                z_score = abs(
                    (
                        numeric_value
                        - mean
                    )
                    / std
                )

                if z_score <= 3:
                    continue

                confidence = round(
                    min(
                        0.99,
                        0.50
                        + (
                            1
                            - np.exp(
                                -(z_score - 3)
                            )
                        )
                    ),
                    2
                )

                if z_score >= 5:
                    severity = "high"
                elif z_score >= 4:
                    severity = "medium"
                else:
                    severity = "low"

                source_row = df.at[
                    index,
                    "_anomai_source_row"
                ] if "_anomai_source_row" in df.columns else (
                    int(index) + 2
                )

                issues.append({
                    "row_index": int(index),
                    "source_row": int(source_row),
                    "column": column,
                    "value": value,
                    "issue_type": "statistical_outlier",
                    "detection_method": "zscore",
                    "severity": severity,
                    "confidence": confidence,
                    "sample_size": sample_count,
                    "z_score": round(
                        float(z_score),
                        4
                    ),
                    "message": (
                        f"Value {value} in column "
                        f"'{column}' has an unusually "
                        f"high absolute z-score of "
                        f"{z_score:.2f}."
                    )
                })

        else:

            raise ValueError(
                f"Unsupported statistical method: {method}"
            )

    return issues