import re


def classify_column(column_name):
    """
    Infer a conservative semantic role from a column name.

    This is not treated as ground truth.
    It is only used to choose safer validation rules.
    """

    name = column_name.lower().strip()

    if re.search(r"\b(email|e_mail|mail)\b", name):
        return "email"

    if re.search(r"\b(age|years_old|employee_age)\b", name):
        return "age"

    if re.search(
        r"\b(salary|income|revenue|amount|price|cost|balance|"
        r"expense|payment|transaction_amount)\b",
        name
    ):
        return "financial"

    if re.search(
        r"\b(id|user_id|customer_id|employee_id|"
        r"account_id|transaction_id)\b",
        name
    ):
        return "identifier"

    if re.search(
        r"\b(date|time|timestamp|created_at|updated_at)\b",
        name
    ):
        return "datetime"

    if re.search(
        r"\b(phone|mobile|telephone)\b",
        name
    ):
        return "phone"

    return "generic"