"""Tests de los handlers de tools de nutrición."""
import json
import importlib


def _reload_tools_nutrition():
    import tools.nutrition as tn
    importlib.reload(tn)
    return tn


def test_log_meal_verifies_persistence(aws, user_id):
    tn = _reload_tools_nutrition()
    result = tn._log_meal(user_id, {
        "description": "avena",
        "calories": 400,
        "meal_type": "desayuno",
    })
    assert "verificada" in result.lower()


def test_get_nutrition_summary_aggregates_by_meal_type(aws, user_id):
    tn = _reload_tools_nutrition()
    aws.put_meal(user_id, "avena", 400, "desayuno", date="2025-05-10")
    aws.put_meal(user_id, "ensalada", 500, "almuerzo", date="2025-05-10")
    aws.put_meal(user_id, "barra", 200, "snack", date="2025-05-10")
    aws.put_meal(user_id, "fruta", 100, "snack", date="2025-05-10")

    result = json.loads(tn._get_nutrition_summary(user_id, {
        "start_date": "2025-05-10",
        "end_date": "2025-05-10",
    }))

    assert result["total_calories"] == 1200
    assert result["count"] == 4
    assert result["by_meal_type"]["snack"]["calories"] == 300
    assert result["by_meal_type"]["snack"]["count"] == 2


def test_get_nutrition_summary_empty(aws, user_id):
    tn = _reload_tools_nutrition()
    result = json.loads(tn._get_nutrition_summary(user_id, {
        "start_date": "2025-05-01",
        "end_date": "2025-05-31",
    }))
    assert result["total_calories"] == 0
    assert result["count"] == 0


def test_update_meal_calories(aws, user_id):
    tn = _reload_tools_nutrition()
    sk = aws.put_meal(user_id, "lunch", 400, "almuerzo")
    result = tn._update_meal(user_id, {"meal_id": sk, "calories": 650})
    assert "actualizada" in result.lower()

    items = aws.query_meals(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["calories"] == 650


def test_delete_meal_verifies(aws, user_id):
    tn = _reload_tools_nutrition()
    sk = aws.put_meal(user_id, "snack", 150, "snack")
    result = tn._delete_meal(user_id, {"meal_id": sk})
    assert "eliminada" in result.lower()
    assert aws.verify_meal_exists(user_id, sk) is False


# ---------------------------------------------------------------------------
# Regresiones — bugs encontrados en logs de prod
# ---------------------------------------------------------------------------

def test_delete_meal_fails_for_nonexistent_id(aws, user_id):
    tn = _reload_tools_nutrition()
    result = tn._delete_meal(user_id, {"meal_id": "fake-id"})
    assert "ERROR" in result
    assert "no existe" in result.lower()


def test_delete_meals_bulk_distinguishes_fake_ids(aws, user_id):
    tn = _reload_tools_nutrition()
    real_sk = aws.put_meal(user_id, "real", 100, "snack")
    fake_ids = ["2026-05-21-01:15-Cono nieve", "2026-05-21-01:15-Ramen"]

    result = tn._delete_meals_bulk(user_id, {"meal_ids": [real_sk, *fake_ids]})
    assert "Eliminadas 1/3" in result
    assert "NO EXISTE" in result
    assert aws.verify_meal_exists(user_id, real_sk) is False


def test_update_meal_rejects_date_field(aws, user_id):
    tn = _reload_tools_nutrition()
    sk = aws.put_meal(user_id, "lunch", 400, "almuerzo")
    result = tn._update_meal(user_id, {"meal_id": sk, "date": "2026-05-20"})
    assert "ERROR" in result
    assert "no editables" in result.lower() or "no son editables" in result.lower()
    # No debe haber cambiado nada
    items = aws.query_meals(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["calories"] == 400


def test_update_meal_partial_with_invalid_field(aws, user_id):
    tn = _reload_tools_nutrition()
    sk = aws.put_meal(user_id, "lunch", 400, "almuerzo")
    result = tn._update_meal(user_id, {
        "meal_id": sk, "calories": 650, "date": "2026-05-20",
    })
    assert "parcialmente" in result.lower()
    items = aws.query_meals(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["calories"] == 650


def test_update_meal_fails_for_nonexistent_id(aws, user_id):
    tn = _reload_tools_nutrition()
    result = tn._update_meal(user_id, {"meal_id": "ghost", "calories": 100})
    assert "ERROR" in result
    assert "no existe" in result.lower()
