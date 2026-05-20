from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key, Attr
from db import _table, _to_float, get_user_id

KST = timezone(timedelta(hours=9))
router = APIRouter()


@router.get("")
def get_summary():
    user_id = get_user_id()
    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y-%m-%d")
    month_start = now_kst.replace(day=1).strftime("%Y-%m-%d")

    # Today expenses
    resp_exp = _table("DYNAMODB_TABLE_EXPENSES").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{today}T00:00:00", f"{today}T23:59:59z"
        )
    )
    today_spend = sum(_to_float(i["amount"]) for i in resp_exp["Items"])

    # Month expenses
    resp_month = _table("DYNAMODB_TABLE_EXPENSES").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{month_start}T00:00:00", f"{today}T23:59:59z"
        )
    )
    month_spend = sum(_to_float(i["amount"]) for i in resp_month["Items"])

    # Month by category
    by_category: dict = {}
    for i in resp_month["Items"]:
        cat = i["category"]
        by_category[cat] = by_category.get(cat, 0) + _to_float(i["amount"])

    # Today calories
    resp_meals = _table("DYNAMODB_TABLE_MEALS").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{today}T00:00:00", f"{today}T23:59:59z"
        )
    )
    today_calories = sum(int(i["calories"]) for i in resp_meals["Items"])

    # Preferences (budget + calorie goal)
    pref_resp = _table("DYNAMODB_TABLE_PREFERENCES").query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    prefs = {item["sk"]: item["value"] for item in pref_resp["Items"]}
    budget_weekly = float(prefs.get("budget_weekly_KRW", 0))
    budget_monthly = float(prefs.get("budget_monthly_KRW", 0))
    calorie_goal = int(prefs.get("calorie_goal_daily", 2200))

    # Pending reminders count
    rem_resp = _table("DYNAMODB_TABLE_REMINDERS").query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("sent").eq(False),
    )
    pending_reminders = len(rem_resp["Items"])

    return {
        "today": {
            "spend": round(today_spend, 2),
            "calories": today_calories,
            "date": today,
        },
        "month": {
            "spend": round(month_spend, 2),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "start": month_start,
        },
        "preferences": {
            "budget_weekly_KRW": budget_weekly,
            "budget_monthly_KRW": budget_monthly,
            "calorie_goal_daily": calorie_goal,
        },
        "pending_reminders": pending_reminders,
    }
