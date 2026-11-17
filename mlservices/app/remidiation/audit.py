from datetime import datetime, timezone
import uuid


def _safe_value(value):

    if value is None:
        return None

    try:

        if hasattr(value, "item"):
            return value.item()

    except Exception:
        pass

    return value


def create_audit_entry(
    action,
    row_index,
    source_row,
    column,
    old_value,
    new_value,
    reason,
    automatic=True
):

    return {
        "audit_id": str(
            uuid.uuid4()
        ),

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "action": action,

        "row_index": (
            int(row_index)
            if row_index is not None
            else None
        ),

        "source_row": (
            int(source_row)
            if source_row is not None
            else None
        ),

        "column": column,

        "old_value": _safe_value(
            old_value
        ),

        "new_value": _safe_value(
            new_value
        ),

        "reason": reason,

        "automatic": bool(
            automatic
        )
    }


def create_audit_trail(
    changes
):

    audit_records = []

    for change in changes:

        audit_records.append(
            create_audit_entry(
                action=change.get(
                    "action"
                ),

                row_index=change.get(
                    "row_index"
                ),

                source_row=change.get(
                    "source_row"
                ),

                column=change.get(
                    "column"
                ),

                old_value=change.get(
                    "old_value"
                ),

                new_value=change.get(
                    "new_value"
                ),

                reason=change.get(
                    "reason"
                ),

                automatic=change.get(
                    "automatic",
                    True
                )
            )
        )

    return audit_records