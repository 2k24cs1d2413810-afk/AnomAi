import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from app.profiling.semantic_classifier import classify_column

MIN_ROWS_FOR_ML = 30
DEFAULT_CONTAMINATION = 0.05

# Internal AnomAI metadata must never be used as ML features.
# These columns are for provenance/audit purposes only.
INTERNAL_COLUMNS = {
    "_anomai_source_row"
}

def _calculate_ml_confidence(anomaly_score, score_min, score_max):
    """
    Convert the relative Isolation Forest anomaly score into
    a bounded evidence-strength heuristic.

    This is NOT a probability.
    """

    if score_max <= score_min:
        return 0.50

    normalized = (
        anomaly_score - score_min
    ) / (score_max - score_min)

    confidence = 0.50 + (0.45 * normalized)

    return round(
        min(max(confidence, 0.50), 0.95),
        2
    )


def _calculate_robust_z_score(series, value):
    """
    Calculate a robust z-score using median and MAD.

    Robust z-scores are less affected by extreme values than
    ordinary mean/std based z-scores.

    This is used only as supporting feature evidence.
    It is NOT a probability.
    """

    numeric_series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(numeric_series) < 3:
        return None

    median = numeric_series.median()

    mad = np.median(
        np.abs(
            numeric_series - median
        )
    )

    if mad == 0 or pd.isna(mad):
        return None

    robust_z = (
        0.6745
        * (float(value) - float(median))
        / float(mad)
    )

    return abs(float(robust_z))


def _build_feature_evidence(df, features_used, row_position):
    """
    Identify numeric features that provide supporting evidence
    for an ML-detected anomalous row.

    ML detection identifies the unusual row.
    This function only explains which features look unusual.
    """

    affected_columns = []

    for column in features_used:

        value = df.iloc[row_position][column]

        if pd.isna(value):
            continue

        robust_z = _calculate_robust_z_score(
            df[column],
            value
        )

        if robust_z is None:
            continue

        if robust_z >= 3:
            evidence_strength = "strong"

        elif robust_z >= 2:
            evidence_strength = "moderate"

        else:
            continue

        affected_columns.append({
            "column": column,
            "value": value,
            "robust_z_score": round(
                robust_z,
                4
            ),
            "evidence_strength": evidence_strength
        })

    return affected_columns


def detect_ml_anomalies(
    df,
    contamination=DEFAULT_CONTAMINATION,
    min_rows=MIN_ROWS_FOR_ML
):
    """
    Detect multivariate anomalies using Isolation Forest.

    ML detection is skipped for small datasets because
    unsupervised anomaly detection is unreliable with very
    small sample sizes.

    Numeric identifier columns are excluded.

    Internal AnomAI metadata columns are excluded.

    RobustScaler is used before model training so the ML
    preprocessing pipeline is explicit and resistant to
    highly skewed numeric distributions.

    Feature-level evidence is calculated separately using
    robust z-scores.
    """

    row_count = len(df)

    # ---------------------------------------------------------
    # 1. Small dataset protection
    # ---------------------------------------------------------

    if row_count < min_rows:

        return {
            "status": "skipped",
            "reason": (
                "Insufficient rows for reliable machine-learning "
                "anomaly detection."
            ),
            "minimum_rows": min_rows,
            "actual_rows": row_count,
            "contamination": contamination,
            "features_used": [],
            "features_skipped": [],
            "issues": []
        }

    # ---------------------------------------------------------
    # 2. Identify numeric columns
    # ---------------------------------------------------------

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    features_used = []
    features_skipped = []

    for column in numeric_columns:

        # Internal AnomAI metadata must never influence
        # anomaly detection.
        if column in INTERNAL_COLUMNS:

            features_skipped.append({
                "column": column,
                "reason": (
                    "Internal AnomAI metadata column excluded "
                    "from ML features."
                )
            })

            continue

        role = classify_column(column)

        # Numeric identifiers should not influence ML because
        # their numerical values have no meaningful magnitude.
        if role == "identifier":

            features_skipped.append({
                "column": column,
                "reason": (
                    "Identifier column excluded from ML features."
                )
            })

            continue

        features_used.append(column)

    # ---------------------------------------------------------
    # 3. No suitable features
    # ---------------------------------------------------------

    if not features_used:

        return {
            "status": "skipped",
            "reason": (
                "No suitable numeric features were available."
            ),
            "minimum_rows": min_rows,
            "actual_rows": row_count,
            "contamination": contamination,
            "features_used": [],
            "features_skipped": features_skipped,
            "issues": []
        }

    # ---------------------------------------------------------
    # 4. Prepare feature matrix
    # ---------------------------------------------------------

    feature_df = df[
        features_used
    ].copy()

    for column in features_used:

        feature_df[column] = pd.to_numeric(
            feature_df[column],
            errors="coerce"
        )

        median = feature_df[column].median()

        if pd.isna(median):
            median = 0

        feature_df[column] = (
            feature_df[column]
            .fillna(median)
        )

    # Remove constant columns.
    # A constant feature provides no useful information
    # for anomaly detection.

    non_constant_features = []

    for column in features_used:

        if feature_df[column].nunique(
            dropna=False
        ) > 1:

            non_constant_features.append(column)

        else:

            features_skipped.append({
                "column": column,
                "reason": (
                    "Constant numeric column excluded because "
                    "it provides no anomaly-detection signal."
                )
            })

    features_used = non_constant_features

    if not features_used:

        return {
            "status": "skipped",
            "reason": (
                "No variable numeric features were available "
                "for machine-learning anomaly detection."
            ),
            "minimum_rows": min_rows,
            "actual_rows": row_count,
            "contamination": contamination,
            "features_used": [],
            "features_skipped": features_skipped,
            "issues": []
        }

    feature_df = feature_df[
        features_used
    ]

    # ---------------------------------------------------------
    # 5. Robust scaling
    # ---------------------------------------------------------

    scaler = RobustScaler()

    scaled_features = scaler.fit_transform(
        feature_df
    )

    scaled_feature_df = pd.DataFrame(
        scaled_features,
        columns=features_used,
        index=df.index
    )

    # ---------------------------------------------------------
    # 6. Normalize contamination safely
    # ---------------------------------------------------------

    contamination = float(
        contamination
    )

    contamination = min(
        max(contamination, 0.01),
        0.20
    )

    # ---------------------------------------------------------
    # 7. Train Isolation Forest
    # ---------------------------------------------------------

    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )

    predictions = model.fit_predict(
        scaled_feature_df
    )

    raw_scores = model.score_samples(
        scaled_feature_df
    )

    # Lower Isolation Forest score means more anomalous.
    # Convert it to a positive anomaly-strength score.

    anomaly_scores = -raw_scores

    score_min = float(
        np.min(anomaly_scores)
    )

    score_max = float(
        np.max(anomaly_scores)
    )

    # ---------------------------------------------------------
    # 8. Build anomaly findings
    # ---------------------------------------------------------

    issues = []

    for position, prediction in enumerate(
        predictions
    ):

        if prediction != -1:
            continue

        row_index = df.index[position]

        anomaly_score = float(
            anomaly_scores[position]
        )

        confidence = _calculate_ml_confidence(
            anomaly_score,
            score_min,
            score_max
        )

        affected_columns = _build_feature_evidence(
            df,
            features_used,
            position
        )

        # ML severity describes strength of the ML signal.
        # It is not a claim that the underlying data value
        # is definitely invalid.

        if confidence >= 0.85:
            severity = "high"

        elif confidence >= 0.70:
            severity = "medium"

        else:
            severity = "low"

        issues.append({
            "row_index": int(row_index),
            "source_row": int(row_index) + 2,
            "column": None,
            "value": None,
            "issue_type": "ml_anomaly",
            "detection_method": "isolation_forest",
            "severity": severity,
            "confidence": confidence,
            "anomaly_score": round(
                anomaly_score,
                6
            ),
            "affected_columns": affected_columns,
            "message": (
                "The row contains a multivariate pattern "
                "that differs from the majority of the dataset. "
                "This is an ML anomaly signal and does not by "
                "itself prove that any individual value is invalid."
            )
        })

    # ---------------------------------------------------------
    # 9. Return complete ML analysis
    # ---------------------------------------------------------

    return {
        "status": "completed",
        "reason": None,
        "minimum_rows": min_rows,
        "actual_rows": row_count,
        "contamination": contamination,
        "features_used": features_used,
        "features_skipped": features_skipped,
        "model": "IsolationForest",
        "n_estimators": 300,
        "preprocessing": "RobustScaler",
        "feature_evidence_method": "robust_z_score",
        "issues": issues
    }