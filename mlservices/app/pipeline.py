from app.utils.file_loader import load_dataset
from app.profiling.profiler import profile_dataset
from app.profiling.statistics import analyze_statistics
from app.anomaly.anomaly_engine import analyze_anomalies
from app.scoring.quality_score import calculate_quality_score
from app.remidiation.suggestions import generate_suggestions
from app.remidiation.cleaner import clean_dataset
from app.remidiation.audit import create_audit_trail


INTERNAL_COLUMNS = {
    "_anomai_source_row"
}


def _remove_internal_columns(df):
    """
    Remove AnomAI internal metadata before returning the
    cleaned dataset to the caller.
    """

    output_df = df.copy(
        deep=True
    )

    columns_to_remove = [
        column
        for column in output_df.columns
        if column in INTERNAL_COLUMNS
    ]

    if columns_to_remove:
        output_df = output_df.drop(
            columns=columns_to_remove
        )

    return output_df


def run_pipeline(
    file_path,
    statistical_method="iqr",
    contamination=0.05
):

    # -----------------------------------------
    # 1. Load
    # -----------------------------------------

    df = load_dataset(
        file_path
    )

    original_df = df.copy(
        deep=True
    )

    # -----------------------------------------
    # 2. Profile
    # -----------------------------------------

    profile = profile_dataset(
        original_df
    )

    # Schema is established before statistics, detection and remediation.
    schema = {
        "rows": int(len(original_df)),
        "columns": [
            {
                "name": item.get("name"),
                "data_type": item.get("data_type"),
                "semantic_role": item.get("semantic_role", "generic"),
                "nullable": bool(item.get("missing_count", 0) > 0),
                "unique_percentage": item.get("unique_percentage", 0)
            }
            for item in profile.get("columns", [])
        ]
    }

    # -----------------------------------------
    # 3. Statistics
    # -----------------------------------------

    statistics = analyze_statistics(
        original_df
    )

    # -----------------------------------------
    # 4. Detection
    # -----------------------------------------

    anomaly_analysis = analyze_anomalies(
        original_df,
        statistical_method=statistical_method,
        contamination=contamination
    )

    findings = anomaly_analysis.get(
        "findings",
        []
    )

    # -----------------------------------------
    # 5. Quality before
    # -----------------------------------------

    quality_before = calculate_quality_score(
        original_df,
        findings
    )

    # -----------------------------------------
    # 6. Suggestions
    # -----------------------------------------

    suggestions = generate_suggestions(
        original_df,
        findings
    )

    # -----------------------------------------
    # 7. Remediation
    # -----------------------------------------

    cleaned_df, changes = clean_dataset(
        original_df,
        findings
    )

    # -----------------------------------------
    # 8. Audit
    # -----------------------------------------

    audit_records = create_audit_trail(
        changes
    )

    # -----------------------------------------
    # 9. Re-analysis
    # -----------------------------------------

    if changes:

        cleaned_anomaly_analysis = (
            analyze_anomalies(
                cleaned_df,
                statistical_method=statistical_method,
                contamination=contamination
            )
        )

        cleaned_findings = (
            cleaned_anomaly_analysis.get(
                "findings",
                []
            )
        )

        quality_after = calculate_quality_score(
            cleaned_df,
            cleaned_findings
        )

    else:

        cleaned_anomaly_analysis = (
            anomaly_analysis
        )

        cleaned_findings = findings

        quality_after = (
            quality_before
        )

    # -----------------------------------------
    # 10. Remove internal metadata
    # -----------------------------------------

    output_cleaned_df = (
        _remove_internal_columns(
            cleaned_df
        )
    )

    # -----------------------------------------
    # 11. Return
    # -----------------------------------------

    return {
        "dataset": {
            "original_rows": len(
                original_df
            ),

            "original_columns": len([
                column
                for column in original_df.columns
                if column not in INTERNAL_COLUMNS
            ]),

            "cleaned_rows": len(
                output_cleaned_df
            ),

            "cleaned_columns": len(
                output_cleaned_df.columns
            ),

            "changes_applied": len(
                changes
            )
        },

        "schema": schema,

        "profile": profile,

        "statistics": statistics,

        "anomalies": {
            "before": anomaly_analysis,
            "after": cleaned_anomaly_analysis
        },

        "quality": {
            "before": quality_before,
            "after": quality_after
        },

        "remidiation": {
            "suggestions": suggestions,
            "changes": changes,
            "audit": audit_records
        },

        "cleaned_data": output_cleaned_df
    }