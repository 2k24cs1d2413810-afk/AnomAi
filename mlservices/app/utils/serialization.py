import math
from datetime import date, datetime

import numpy as np
import pandas as pd


def make_json_safe(value):
    """
    Recursively convert Python, NumPy and pandas values
    into values that can be safely serialized as JSON.
    """

    if value is None:
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        float_value = float(value)

        if math.isnan(float_value) or math.isinf(float_value):
            return None

        return float_value

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, np.ndarray):
        return [
            make_json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, pd.Series):
        return [
            make_json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, pd.DataFrame):
        return make_json_safe(
            value.to_dict(
                orient="records"
            )
        )

    return value