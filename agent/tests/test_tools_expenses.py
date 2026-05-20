"""Tests de los handlers de tools de gastos."""
import json
import importlib


def _reload_tools_expenses():
    """Recarga tools.expenses con el storage mockeado vigente."""
    import tools.expenses as te
    importlib.reload(te)
    return te


def test_save_expense_verifies_persistence(aws, user_id):
    te = _reload_tools_expenses()
    result = te._save_expense(user_id, {
        "amount": 15000,
        "category": "comida",
        "description": "ramen",
        "currency": "KRW",
    })
    assert "verificado" in result.lower()
    # Y debe existir en DynamoDB
    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert len(items) == 1


def test_get_expense_summary_aggregates_by_currency_and_category(aws, user_id):
    te = _reload_tools_expenses()
    aws.put_expense(user_id, 1000, "comida", "a", "KRW", date="2025-05-10")
    aws.put_expense(user_id, 2000, "comida", "b", "KRW", date="2025-05-11")
    aws.put_expense(user_id, 50, "transporte", "uber", "USD", date="2025-05-12")

    result = json.loads(te._get_expense_summary(user_id, {
        "start_date": "2025-05-01",
        "end_date": "2025-05-31",
    }))

    assert result["count"] == 3
    assert result["totals_by_currency"]["KRW"] == 3000
    assert result["totals_by_currency"]["USD"] == 50
    assert result["by_category"]["comida"]["KRW"] == 3000
    assert result["by_category"]["transporte"]["USD"] == 50


def test_get_expense_summary_empty_range(aws, user_id):
    te = _reload_tools_expenses()
    result = json.loads(te._get_expense_summary(user_id, {
        "start_date": "2025-05-01",
        "end_date": "2025-05-31",
    }))
    assert result["count"] == 0
    assert result["totals_by_currency"] == {}


def test_get_recent_expenses_caps_at_10(aws, user_id):
    te = _reload_tools_expenses()
    for i in range(15):
        aws.put_expense(user_id, i + 1, "comida", f"e{i}", "USD", date=f"2025-05-{i+1:02d}")

    # limit=50 debe quedar capeado en 10
    result = json.loads(te._get_recent_expenses(user_id, {"limit": 50}))
    assert result["count"] == 10


def test_update_expense_with_no_changeable_fields(aws, user_id):
    te = _reload_tools_expenses()
    sk = aws.put_expense(user_id, 100, "comida", "x", "USD")
    result = te._update_expense(user_id, {"expense_id": sk})
    assert "No se especificaron campos" in result


def test_update_expense_reports_success_when_exists(aws, user_id):
    te = _reload_tools_expenses()
    sk = aws.put_expense(user_id, 100, "comida", "x", "USD")
    result = te._update_expense(user_id, {"expense_id": sk, "amount": 200})
    assert "actualizado" in result.lower()
    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["amount"] == 200.0


def test_delete_expense_verifies_deletion(aws, user_id):
    te = _reload_tools_expenses()
    sk = aws.put_expense(user_id, 100, "comida", "x", "USD")
    result = te._delete_expense(user_id, {"expense_id": sk})
    assert "eliminado" in result.lower()
    assert aws.verify_expense_exists(user_id, sk) is False


def test_delete_expenses_bulk_reports_count(aws, user_id):
    te = _reload_tools_expenses()
    sks = [aws.put_expense(user_id, 10, "comida", f"x{i}", "USD") for i in range(3)]
    # Más un id falso que no existe (delete es idempotente, debería contar como éxito porque verify=False)
    result = te._delete_expenses_bulk(user_id, {"expense_ids": sks})
    assert "3/3" in result
    for sk in sks:
        assert aws.verify_expense_exists(user_id, sk) is False
