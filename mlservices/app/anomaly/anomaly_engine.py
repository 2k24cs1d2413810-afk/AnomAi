from app.anomaly.rule_detector import detect_rule_violations
from app.anomaly.statistical_detector import detect_statistical_anomalies
from app.anomaly.ml_detector import detect_ml_anomalies


def _severity_rank(severity):
    """
    Convert severity into a numeric rank so that when multiple
    detectors report the same finding, the strongest severity
    is retained.
    """

    ranks = {
        "low": 1,
        "medium": 2,
        "high": 3
    }

    return ranks.get(severity, 0)


def _highest_severity(issues):
    """
    Return the highest severity among detector evidence.
    """

    if not issues:
        return "low"

    return max(
        (
            issue.get("severity", "low")
            for issue in issues
        ),
        key=_severity_rank
    )


def _calculate_combined_confidence(issues):
    """
    Combine detector confidence values.

    This is an evidence-strength heuristic, NOT a probability.
    """

    if not issues:
        return 0.0

    confidences = []

    for issue in issues:

        confidence = issue.get("confidence")

        if confidence is None:
            continue

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            continue

        confidence = min(
            max(confidence, 0.0),
            0.99
        )

        confidences.append(confidence)

    if not confidences:
        return 0.0

    # Independent evidence should increase evidence strength,
    # but never reach absolute certainty.
    combined = 1.0

    for confidence in confidences:
        combined *= (1.0 - confidence)

    combined = 1.0 - combined

    return round(
        min(combined, 0.99),
        2
    )


def _build_evidence_record(issue):
    """
    Convert a raw detector result into a compact evidence record.

    Detector-specific evidence is preserved so that the final
    finding remains explainable and traceable.
    """

    evidence = {
        "detection_method": issue.get(
            "detection_method"
        ),
        "issue_type": issue.get(
            "issue_type"
        ),
        "severity": issue.get(
            "severity"
        ),
        "confidence": issue.get(
            "confidence"
        ),
        "message": issue.get(
            "message"
        )
    }

    # ---------------------------------------------------------
    # Statistical evidence
    # ---------------------------------------------------------

    if issue.get("expected_range") is not None:

        evidence["expected_range"] = issue.get(
            "expected_range"
        )

    if issue.get("distance_ratio") is not None:

        evidence["distance_ratio"] = issue.get(
            "distance_ratio"
        )

    if issue.get("z_score") is not None:

        evidence["z_score"] = issue.get(
            "z_score"
        )

    # ---------------------------------------------------------
    # ML evidence
    # ---------------------------------------------------------

    if issue.get("anomaly_score") is not None:

        evidence["anomaly_score"] = issue.get(
            "anomaly_score"
        )

    if issue.get("affected_columns"):

        evidence["affected_columns"] = issue.get(
            "affected_columns"
        )

    return evidence


def _group_key(issue):
    """
    Determine which raw detector results refer to the same
    underlying cell-level finding.

    Rule and statistical evidence for the same row/column
    are grouped together.

    ML findings are row-level evidence and remain separate.
    """

    detection_method = issue.get(
        "detection_method"
    )

    row_index = issue.get(
        "row_index"
    )

    column = issue.get(
        "column"
    )

    # ML anomalies are multivariate row-level findings.
    if detection_method == "isolation_forest":

        return (
            "row",
            row_index,
            "ml_anomaly"
        )

    # Cell-level findings are grouped by row and column.
    return (
        "cell",
        row_index,
        column
    )


def _aggregate_findings(issues):
    """
    Combine multiple detector outputs referring to the same
    row/cell into one unified finding.
    """

    groups = {}

    for issue in issues:

        key = _group_key(issue)

        if key not in groups:
            groups[key] = []

        groups[key].append(issue)

    findings = []

    for grouped_issues in groups.values():

        primary = grouped_issues[0]

        evidence = [
            _build_evidence_record(issue)
            for issue in grouped_issues
        ]

        issue_types = sorted({
            issue.get("issue_type")
            for issue in grouped_issues
            if issue.get("issue_type")
        })

        detection_methods = sorted({
            issue.get("detection_method")
            for issue in grouped_issues
            if issue.get("detection_method")
        })

        finding = {
            "row_index": primary.get(
                "row_index"
            ),

            "source_row": primary.get(
                "source_row"
            ),

            "column": primary.get(
                "column"
            ),

            "value": primary.get(
                "value"
            ),

            "issue_type": (
                issue_types[0]
                if len(issue_types) == 1
                else "combined_data_quality_issue"
            ),

            "issue_types": issue_types,

            "detection_methods": detection_methods,

            "severity": _highest_severity(
                grouped_issues
            ),

            "confidence": _calculate_combined_confidence(
                grouped_issues
            ),

            "evidence_count": len(
                evidence
            ),

            "evidence": evidence,

            "message": (
                f"{len(grouped_issues)} detection "
                f"signals identify an issue at "
                f"row {primary.get('source_row')}."
            )
        }

        # -----------------------------------------------------
        # Preserve ML-specific feature evidence at the
        # finding level as well.
        # -----------------------------------------------------

        affected_columns = []

        for issue in grouped_issues:

            ml_columns = issue.get(
                "affected_columns",
                []
            )

            if ml_columns:

                affected_columns.extend(
                    ml_columns
                )

        if affected_columns:

            finding["affected_columns"] = (
                affected_columns
            )

        findings.append(
            finding
        )

    findings.sort(
        key=lambda finding: (
            finding.get(
                "row_index",
                -1
            ),
            str(
                finding.get(
                    "column"
                )
            )
        )
    )

    return findings


def _build_summary(
    raw_evidence,
    findings,
    ml_analysis
):
    """
    Build separate detector-evidence and unified-finding metrics.
    """

    rule_evidence = [
        issue
        for issue in raw_evidence
        if issue.get(
            "detection_method"
        ) == "rule"
    ]

    statistical_evidence = [
        issue
        for issue in raw_evidence
        if issue.get(
            "detection_method"
        ) in {
            "iqr",
            "zscore"
        }
    ]

    ml_evidence = [
        issue
        for issue in raw_evidence
        if issue.get(
            "detection_method"
        ) == "isolation_forest"
    ]

    affected_rows = {
        finding.get(
            "row_index"
        )
        for finding in findings
        if finding.get(
            "row_index"
        ) is not None
    }

    affected_cells = {
        (
            finding.get(
                "row_index"
            ),
            finding.get(
                "column"
            )
        )
        for finding in findings
        if (
            finding.get(
                "row_index"
            ) is not None
            and finding.get(
                "column"
            ) is not None
        )
    }

    high_severity = [
        finding
        for finding in findings
        if finding.get(
            "severity"
        ) == "high"
    ]

    medium_severity = [
        finding
        for finding in findings
        if finding.get(
            "severity"
        ) == "medium"
    ]

    low_severity = [
        finding
        for finding in findings
        if finding.get(
            "severity"
        ) == "low"
    ]

    return {
        # -----------------------------------------------------
        # Raw detector evidence
        # -----------------------------------------------------

        "total_evidence": len(
            raw_evidence
        ),

        "rule_evidence": len(
            rule_evidence
        ),

        "statistical_evidence": len(
            statistical_evidence
        ),

        "ml_evidence": len(
            ml_evidence
        ),

        # -----------------------------------------------------
        # Unified findings
        # -----------------------------------------------------

        "unique_findings": len(
            findings
        ),

        "affected_rows": len(
            affected_rows
        ),

        "affected_cells": len(
            affected_cells
        ),

        "high_severity": len(
            high_severity
        ),

        "medium_severity": len(
            medium_severity
        ),

        "low_severity": len(
            low_severity
        ),

        # -----------------------------------------------------
        # ML execution state
        # -----------------------------------------------------

        "ml_status": ml_analysis.get(
            "status"
        ),

        "ml_reason": ml_analysis.get(
            "reason"
        )
    }


def analyze_anomalies(
    df,
    statistical_method="iqr",
    contamination=0.05
):
    """
    Run all detectors and produce both raw evidence and
    unified findings.
    """

    # ---------------------------------------------------------
    # Rule detection
    # ---------------------------------------------------------

    rule_issues = detect_rule_violations(
        df
    )

    # ---------------------------------------------------------
    # Statistical detection
    # ---------------------------------------------------------

    statistical_issues = detect_statistical_anomalies(
        df,
        method=statistical_method
    )

    # ---------------------------------------------------------
    # ML detection
    # ---------------------------------------------------------

    ml_analysis = detect_ml_anomalies(
        df,
        contamination=contamination
    )

    ml_issues = ml_analysis.get(
        "issues",
        []
    )

    # ---------------------------------------------------------
    # Combine raw evidence
    # ---------------------------------------------------------

    raw_evidence = (
        rule_issues
        + statistical_issues
        + ml_issues
    )

    # ---------------------------------------------------------
    # Remove exact duplicate detector records
    # ---------------------------------------------------------

    unique_evidence = []

    seen = set()

    for issue in raw_evidence:

        key = (
            issue.get("row_index"),
            issue.get("column"),
            issue.get("issue_type"),
            issue.get("detection_method")
        )

        if key in seen:
            continue

        seen.add(key)

        unique_evidence.append(
            issue
        )

    # ---------------------------------------------------------
    # Aggregate evidence into findings
    # ---------------------------------------------------------

    findings = _aggregate_findings(
        unique_evidence
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary = _build_summary(
        unique_evidence,
        findings,
        ml_analysis
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return {
        # Raw evidence is preserved for debugging/audit.
        "evidence": unique_evidence,

        # Unified user-facing findings.
        "findings": findings,

        # Backward compatibility for current pipeline.
        "issues": unique_evidence,

        "summary": summary,

        # -----------------------------------------------------
        # ML analysis metadata
        # -----------------------------------------------------

        "ml_analysis": {
            "status": ml_analysis.get(
                "status"
            ),

            "reason": ml_analysis.get(
                "reason"
            ),

            "minimum_rows": ml_analysis.get(
                "minimum_rows"
            ),

            "actual_rows": ml_analysis.get(
                "actual_rows"
            ),

            "contamination": ml_analysis.get(
                "contamination"
            ),

            "features_used": ml_analysis.get(
                "features_used",
                []
            ),

            "features_skipped": ml_analysis.get(
                "features_skipped",
                []
            ),

            "model": ml_analysis.get(
                "model"
            ),

            "n_estimators": ml_analysis.get(
                "n_estimators"
            ),

            # New: preserve ML preprocessing provenance.
            "preprocessing": ml_analysis.get(
                "preprocessing"
            ),

            # New: preserve the method used to explain
            # which features contributed to the ML signal.
            "feature_evidence_method": ml_analysis.get(
                "feature_evidence_method"
            )
        }
    }