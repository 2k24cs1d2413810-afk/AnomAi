import pandas as pd


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _valid_numeric_values(df, column):
    """
    Return valid numeric values from a column.
    """

    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()


def _suggest_age_correction(df, column):
    """
    Generate a review-only suggestion for an invalid age.

    The value is never automatically replaced.
    """

    values = _valid_numeric_values(
        df,
        column
    )

    valid_values = values[
        (values >= 0)
        & (values <= 120)
    ]

    if valid_values.empty:

        return {
            "action": "manual_review",
            "suggested_value": None,
            "confidence": 0.90,
            "requires_review": True,
            "reason": (
                "The age is outside the valid range, but "
                "there are not enough valid age values to "
                "generate a reliable correction suggestion."
            )
        }

    suggested_value = valid_values.median()

    # Ages are generally represented as whole numbers.
    suggested_value = int(round(suggested_value))

    return {
        "action": "suggest_value",
        "suggested_value": suggested_value,
        "confidence": 0.85,
        "requires_review": True,
        "reason": (
            "The age is outside the valid range 0-120. "
            "The median of valid age values is provided only "
            "as a review suggestion; it is not automatically "
            "applied."
        )
    }


def _suggest_statistical_review(finding):
    """
    Generate a review-only suggestion for a statistical anomaly.
    """

    expected_range = finding.get(
        "evidence",
        []
    )

    range_value = None

    for evidence in expected_range:

        if evidence.get("expected_range") is not None:
            range_value = evidence.get(
                "expected_range"
            )
            break

    return {
        "action": "manual_review",
        "suggested_value": None,
        "confidence": finding.get(
            "confidence",
            0.50
        ),
        "requires_review": True,
        "reason": (
            "The value is statistically unusual and "
            "requires review."
            + (
                f" Expected range: {range_value}."
                if range_value is not None
                else ""
            )
        )
    }


def generate_suggestions(df, findings):
    """
    Generate remediation suggestions from unified findings.

    Suggestions are deliberately conservative:
    uncertain values are never automatically invented.
    """

    suggestions = []

    for finding in findings:

        issue_types = set(
            finding.get(
                "issue_types",
                []
            )
        )

        row_index = finding.get(
            "row_index"
        )

        column = finding.get(
            "column"
        )

        issue_type = finding.get(
            "issue_type"
        )

        suggestion = None

        # -----------------------------------------------------
        # Missing values
        # -----------------------------------------------------

        if "missing_value" in issue_types:

            if column in df.columns:

                series = df[column]

                if pd.api.types.is_numeric_dtype(
                    series
                ):

                    numeric_values = pd.to_numeric(
                        series,
                        errors="coerce"
                    ).dropna()

                    if not numeric_values.empty:

                        suggested_value = (
                            numeric_values.median()
                        )

                        suggestion = {
                            "action": "suggest_value",
                            "suggested_value": (
                                suggested_value
                            ),
                            "confidence": 0.75,
                            "requires_review": True,
                            "reason": (
                                "Median value suggested "
                                "for review because the "
                                "original value is missing."
                            )
                        }

                else:

                    mode = series.mode()

                    if not mode.empty:

                        suggestion = {
                            "action": "suggest_value",
                            "suggested_value": (
                                mode.iloc[0]
                            ),
                            "confidence": 0.65,
                            "requires_review": True,
                            "reason": (
                                "Most frequent value "
                                "suggested for review "
                                "because the original "
                                "value is missing."
                            )
                        }

        # -----------------------------------------------------
        # Invalid age
        # -----------------------------------------------------

        elif "invalid_age" in issue_types:

            suggestion = _suggest_age_correction(
                df,
                column
            )

        # -----------------------------------------------------
        # Invalid email
        # -----------------------------------------------------

        elif "invalid_email" in issue_types:

            suggestion = {
                "action": "manual_review",
                "suggested_value": None,
                "confidence": 0.95,
                "requires_review": True,
                "reason": (
                    "The email format is invalid, but "
                    "the correct email address cannot be "
                    "reliably inferred."
                )
            }

        # -----------------------------------------------------
        # Negative financial value
        # -----------------------------------------------------

        elif "negative_value" in issue_types:

            suggestion = {
                "action": "manual_review",
                "suggested_value": None,
                "confidence": 0.90,
                "requires_review": True,
                "reason": (
                    "The value is negative, but the intended "
                    "value cannot safely be inferred."
                )
            }

        # -----------------------------------------------------
        # Statistical anomaly
        # -----------------------------------------------------

        elif "statistical_outlier" in issue_types:

            suggestion = _suggest_statistical_review(
                finding
            )

        # -----------------------------------------------------
        # ML anomaly
        # -----------------------------------------------------

        elif "ml_anomaly" in issue_types:

            suggestion = {
                "action": "manual_review",
                "suggested_value": None,
                "confidence": finding.get(
                    "confidence",
                    0.50
                ),
                "requires_review": True,
                "reason": (
                    "The row contains a multivariate pattern "
                    "that differs from the majority of the "
                    "dataset. The ML detector does not "
                    "determine a specific correction."
                )
            }

        # -----------------------------------------------------
        # Unknown issue
        # -----------------------------------------------------

        else:

            suggestion = {
                "action": "manual_review",
                "suggested_value": None,
                "confidence": 0.50,
                "requires_review": True,
                "reason": (
                    "No automatic remediation strategy is "
                    "currently available."
                )
            }

        if suggestion is None:
            continue

        suggestions.append({
            "row_index": row_index,
            "column": column,
            "issue_type": issue_type,
            "issue_types": sorted(issue_types),
            "action": suggestion["action"],
            "suggested_value": suggestion[
                "suggested_value"
            ],
            "confidence": suggestion[
                "confidence"
            ],
            "requires_review": suggestion[
                "requires_review"
            ],
            "reason": suggestion[
                "reason"
            ]
        })

    return suggestions