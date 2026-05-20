"""Tests del módulo storage para gastos."""


def test_put_and_query_expense(aws, user_id):
    sk = aws.put_expense(user_id, 15000, "comida", "ramen", "krw")
    assert sk

    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert len(items) == 1
    assert items[0]["amount"] == 15000.0
    assert items[0]["category"] == "comida"
    # Las monedas se normalizan a mayúsculas
    assert items[0]["currency"] == "KRW"


def test_put_expense_with_explicit_date(aws, user_id):
    sk = aws.put_expense(user_id, 100, "transporte", "uber", "USD", date="2025-06-15")
    assert sk.startswith("2025-06-15T00:00:00#")

    items = aws.query_expenses(user_id, "2025-06-15", "2025-06-15")
    assert len(items) == 1
    assert items[0]["date"] == "2025-06-15"


def test_query_expenses_respects_date_range(aws, user_id):
    aws.put_expense(user_id, 1, "comida", "a", "USD", date="2025-01-10")
    aws.put_expense(user_id, 2, "comida", "b", "USD", date="2025-02-15")
    aws.put_expense(user_id, 3, "comida", "c", "USD", date="2025-03-20")

    items = aws.query_expenses(user_id, "2025-02-01", "2025-02-28")
    assert len(items) == 1
    assert items[0]["description"] == "b"


def test_verify_expense_exists(aws, user_id):
    sk = aws.put_expense(user_id, 50, "comida", "test", "USD")
    assert aws.verify_expense_exists(user_id, sk) is True
    assert aws.verify_expense_exists(user_id, "fake-sk") is False


def test_delete_expense(aws, user_id):
    sk = aws.put_expense(user_id, 50, "comida", "test", "USD")
    assert aws.verify_expense_exists(user_id, sk) is True

    aws.delete_expense(user_id, sk)
    assert aws.verify_expense_exists(user_id, sk) is False


def test_update_expense_partial_fields(aws, user_id):
    sk = aws.put_expense(user_id, 100, "comida", "original", "USD")
    aws.update_expense(user_id, sk, {"amount": 200, "description": "updated"})

    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["amount"] == 200.0
    assert items[0]["description"] == "updated"
    # category y currency no cambiaron
    assert items[0]["category"] == "comida"
    assert items[0]["currency"] == "USD"


def test_update_expense_with_no_fields_is_noop(aws, user_id):
    sk = aws.put_expense(user_id, 100, "comida", "x", "USD")
    aws.update_expense(user_id, sk, {})  # no debería romper
    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["amount"] == 100.0


def test_get_recent_expenses_returns_newest_first(aws, user_id):
    aws.put_expense(user_id, 1, "comida", "old", "USD", date="2025-01-01")
    aws.put_expense(user_id, 2, "comida", "mid", "USD", date="2025-06-01")
    aws.put_expense(user_id, 3, "comida", "new", "USD", date="2025-12-01")

    recent = aws.get_recent_expenses(user_id, limit=2)
    assert len(recent) == 2
    assert recent[0]["description"] == "new"
    assert recent[1]["description"] == "mid"
    # Debe incluir el id (sk) para poder borrar/actualizar
    assert "id" in recent[0]


def test_user_isolation(aws, user_id):
    aws.put_expense(user_id, 100, "comida", "mine", "USD")
    aws.put_expense("other-user", 999, "comida", "theirs", "USD")

    items = aws.query_expenses(user_id, "2020-01-01", "2099-12-31")
    assert len(items) == 1
    assert items[0]["description"] == "mine"
