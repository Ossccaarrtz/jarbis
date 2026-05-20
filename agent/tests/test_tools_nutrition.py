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
