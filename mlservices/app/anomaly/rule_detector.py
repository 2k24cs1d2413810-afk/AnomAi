import re

import pandas as pd

from app.profiling.semantic_classifier import classify_column


INTERNAL_COLUMNS = {
    "_anomai_source_row"
}


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def detect_rule_violations(df):
    """
    Detect deterministic data-quality violations.
    """

    issues = []

    for index, row in df.iterrows():

        source_row = row.get(
            "_anomai_source_row"
        )

        for column in df.columns:

            if column in INTERNAL_COLUMNS:
                continue

            value = row[column]

            role = classify_column(
                column
            )

            # Missing value
            if pd.isna(value):

                issues.append({
                    "row_index": int(index),
                    "source_row": (
                        int(source_row)
                        if pd.notna(source_row)
                        else int(index) + 2
                    ),
                    "column": column,
                    "value": None,
                    "issue_type": "missing_value",
                    "detection_method": "rule",
                    "severity": "medium",
                    "confidence": 1.0,
                    "message": (
                        f"Missing value detected in "
                        f"column '{column}'."
                    )
                })

                continue

            # Email
            if role == "email":

                value_string = str(
                    value
                ).strip()

                if not EMAIL_PATTERN.fullmatch(
                    value_string
                ):

                    issues.append({
                        "row_index": int(index),
                        "source_row": (
                            int(source_row)
                            if pd.notna(source_row)
                            else int(index) + 2
                        ),
                        "column": column,
                        "value": value_string,
                        "issue_type": "invalid_email",
                        "detection_method": "rule",
                        "severity": "medium",
                        "confidence": 0.99,
                        "message": (
                            f"Invalid email format detected "
                            f"in column '{column}'."
                        )
                    })

            # Age
            elif role == "age":

                try:

                    age = float(value)

                    if age < 0 or age > 120:

                        issues.append({
                            "row_index": int(index),
                            "source_row": (
                                int(source_row)
                                if pd.notna(source_row)
                                else int(index) + 2
                            ),
                            "column": column,
                            "value": value,
                            "issue_type": "invalid_age",
                            "detection_method": "rule",
                            "severity": "high",
                            "confidence": 0.99,
                            "expected_range": {
                                "lower": 0,
                                "upper": 120
                            },
                            "message": (
                                f"Age value {value} is "
                                f"outside the valid range 0-120."
                            )
                        })

                except (
                    TypeError,
                    ValueError
                ):
                    pass

            # Financial
            elif role == "financial":

                try:

                    amount = float(value)

                    if amount < 0:

                        issues.append({
                            "row_index": int(index),
                            "source_row": (
                                int(source_row)
                                if pd.notna(source_row)
                                else int(index) + 2
                            ),
                            "column": column,
                            "value": value,
                            "issue_type": "negative_value",
                            "detection_method": "rule",
                            "severity": "high",
                            "confidence": 0.90,
                            "message": (
                                f"Negative financial value "
                                f"detected in column '{column}'."
                            )
                        })

                except (
                    TypeError,
                    ValueError
                ):
                    pass

    return issues