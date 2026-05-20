"""Tests del módulo storage para comidas y preferencias."""


def test_put_and_query_meal(aws, user_id):
    sk = aws.put_meal(user_id, "avena con fruta", 400, "DESAYUNO")
    assert sk

    items = aws.query_meals(user_id, "2020-01-01", "2099-12-31")
    assert len(items) == 1
    assert items[0]["calories"] == 400
    # meal_type se normaliza a minúsculas
    assert items[0]["meal_type"] == "desayuno"


def test_update_meal_partial_fields(aws, user_id):
    sk = aws.put_meal(user_id, "lunch", 400, "almuerzo")
    aws.update_meal(user_id, sk, {"calories": 650})

    items = aws.query_meals(user_id, "2020-01-01", "2099-12-31")
    assert items[0]["calories"] == 650
    assert items[0]["description"] == "lunch"  # sin cambios


def test_delete_meal_and_verify(aws, user_id):
    sk = aws.put_meal(user_id, "snack", 150, "snack")
    assert aws.verify_meal_exists(user_id, sk) is True

    aws.delete_meal(user_id, sk)
    assert aws.verify_meal_exists(user_id, sk) is False


def test_preferences_put_and_get(aws, user_id):
    aws.put_preference(user_id, "budget_monthly_KRW", "800000")
    assert aws.get_preference(user_id, "budget_monthly_KRW") == "800000"
    assert aws.get_preference(user_id, "nonexistent") is None


def test_get_all_preferences(aws, user_id):
    aws.put_preference(user_id, "budget_monthly_KRW", "800000")
    aws.put_preference(user_id, "calorie_goal_daily", "2200")
    aws.put_preference(user_id, "timezone", "Asia/Seoul")

    prefs = aws.get_all_preferences(user_id)
    assert prefs == {
        "budget_monthly_KRW": "800000",
        "calorie_goal_daily": "2200",
        "timezone": "Asia/Seoul",
    }
