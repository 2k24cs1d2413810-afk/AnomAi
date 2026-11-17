INTERNAL_COLUMNS = { 
    "_anomai_source_row" 
} 
 
 
def _severity_weight(severity): 
 
    weights = { 
        "low": 1.0, 
        "medium": 1.5, 
        "high": 2.0 
    } 
 
    return weights.get( 
        severity, 
        1.0 
    ) 
 
 
def _calculate_completeness( 
    df, 
    data_columns 
): 
 
    total_cells = ( 
        len(df) 
        * len(data_columns) 
    ) 
 
    if total_cells == 0: 
        return 100.0, 0 
 
    missing_cells = int( 
        df[data_columns] 
        .isna() 
        .sum() 
        .sum() 
    ) 
 
    completeness = ( 
        100 
        * ( 
            1 
            - ( 
                missing_cells 
                / total_cells 
            ) 
        ) 
    ) 
 
    return round( 
        completeness, 
        2 
    ), missing_cells 
 
 
def _calculate_uniqueness( 
    df, 
    data_columns 
): 
 
    total_rows = len(df) 
 
    if total_rows == 0: 
        return 100.0, 0 
 
    # If there are no actual data columns, there is no 
    # meaningful basis for duplicate-row analysis. 
    if not data_columns: 
        return 100.0, 0 
 
    duplicate_rows = int( 
        df[data_columns] 
        .duplicated() 
        .sum() 
    ) 
 
    uniqueness = ( 
        100 
        * ( 
            1 
            - ( 
                duplicate_rows 
                / total_rows 
            ) 
        ) 
    ) 
 
    return round( 
        uniqueness, 
        2 
    ), duplicate_rows 
 
 
def _calculate_validity( 
    findings, 
    total_cells 
): 
 
    rule_findings = [] 
 
    for finding in findings: 
 
        detection_methods = finding.get( 
            "detection_methods", 
            [] 
        ) 
 
        if "rule" in detection_methods: 
 
            rule_findings.append( 
                finding 
            ) 
 
    if total_cells == 0: 
        return 100.0, 0, 0.0, 0.0 
 
    weighted_penalty = 0.0 
 
    for finding in rule_findings: 
 
        weighted_penalty += ( 
            _severity_weight( 
                finding.get( 
                    "severity", 
                    "medium" 
                ) 
            ) 
        ) 
 
    validity_issue_rate = ( 
        weighted_penalty 
        / total_cells 
    ) 
 
    validity = 100 - ( 
        validity_issue_rate 
        * 100 
    ) 
 
    validity = max( 
        0.0, 
        validity 
    ) 
 
    return ( 
        round(validity, 2), 
        len(rule_findings), 
        round(weighted_penalty, 2), 
        round( 
            validity_issue_rate * 100, 
            2 
        ) 
    ) 
 
 
def _calculate_anomaly_score( 
    findings, 
    total_rows 
): 
 
    if total_rows == 0: 
        return 100.0, 0, 0.0 
 
    affected_rows = set() 
 
    for finding in findings: 
 
        row_index = finding.get( 
            "row_index" 
        ) 
 
        if row_index is not None: 
 
            affected_rows.add( 
                row_index 
            ) 
 
    affected_row_count = len( 
        affected_rows 
    ) 
 
    affected_row_rate = ( 
        affected_row_count 
        / total_rows 
    ) 
 
    anomaly_score = ( 
        100 
        - ( 
            affected_row_rate 
            * 100 
        ) 
    ) 
 
    return ( 
        round( 
            max( 
                anomaly_score, 
                0.0 
            ), 
            2 
        ), 
        affected_row_count, 
        round( 
            affected_row_rate * 100, 
            2 
        ) 
    ) 
 
 
def calculate_quality_score( 
    df, 
    findings 
): 
 
    data_columns = [ 
        column 
        for column in df.columns 
        if column not in INTERNAL_COLUMNS 
    ] 
 
    total_rows = len(df) 
 
    total_columns = len( 
        data_columns 
    ) 
 
    total_cells = ( 
        total_rows 
        * total_columns 
    ) 
 
    completeness, missing_cells = ( 
        _calculate_completeness( 
            df, 
            data_columns 
        ) 
    ) 
 
    uniqueness, duplicate_rows = ( 
        _calculate_uniqueness( 
            df, 
            data_columns 
        ) 
    ) 
 
    ( 
        validity, 
        validity_issues, 
        validity_penalty, 
        validity_issue_rate 
    ) = _calculate_validity( 
        findings, 
        total_cells 
    ) 
 
    ( 
        anomaly_score, 
        affected_rows, 
        affected_row_rate 
    ) = _calculate_anomaly_score( 
        findings, 
        total_rows 
    ) 
 
    overall_score = ( 
        completeness * 0.25 
        + validity * 0.30 
        + uniqueness * 0.15 
        + anomaly_score * 0.30 
    ) 
 
    overall_score = round( 
        overall_score, 
        2 
    ) 
 
    if overall_score >= 90: 
 
        interpretation = ( 
            "High reliability" 
        ) 
 
    elif overall_score >= 75: 
 
        interpretation = ( 
            "Good reliability" 
        ) 
 
    elif overall_score >= 50: 
 
        interpretation = ( 
            "Moderate reliability" 
        ) 
 
    else: 
 
        interpretation = ( 
            "Low reliability" 
        ) 
 
    return { 
        "overall_score": overall_score, 
 
        "dimensions": { 
            "completeness": completeness, 
            "validity": validity, 
            "uniqueness": uniqueness, 
            "anomaly_score": anomaly_score 
        }, 
 
        "metrics": { 
            "total_cells": total_cells, 
            "missing_cells": missing_cells, 
 
            "validity_issues": validity_issues, 
            "validity_penalty": validity_penalty, 
            "validity_issue_rate": validity_issue_rate, 
 
            "duplicate_rows": duplicate_rows, 
 
            "affected_rows": affected_rows, 
            "affected_row_rate": affected_row_rate, 
 
            "total_rows": total_rows, 
            "total_columns": total_columns 
        }, 
 
        "interpretation": interpretation 
    }