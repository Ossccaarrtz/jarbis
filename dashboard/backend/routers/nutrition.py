from fastapi import APIRouter, Query
from boto3.dynamodb.conditions import Key
from db import _table, _to_float, get_user_id
from datetime import date, timedelta
from decimal import Decimal

router = APIRouter()


def _parse_meals(items: list) -> list:
    return [
        {
            "id": item["sk"],
            "date": item["sk"][:10],
            "time": item["sk"][11:16],
            "description": item["description"],
            "calories": int(item["calories"]),
            "meal_type": item["meal_type"],
        }
        for item in items
    ]


@router.get("")
def get_nutrition(
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
):
    user_id = get_user_id()
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    response = _table("DYNAMODB_TABLE_MEALS").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{start_date}T00:00:00",
            f"{end_date}T23:59:59z",
        )
    )
    items = _parse_meals(response["Items"])
    total_calories = sum(i["calories"] for i in items)
    by_type: dict = {}
    for i in items:
        by_type.setdefault(i["meal_type"], []).append(i)

    return {
        "items": sorted(items, key=lambda x: x["date"] + x["time"], reverse=True),
        "total_calories": total_calories,
        "by_meal_type": by_type,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get("/today")
def get_today_nutrition():
    today = date.today().isoformat()
    return get_nutrition(start_date=today, end_date=today)


@router.get("/weekly")
def get_weekly_nutrition():
    today = date.today()
    days = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        resp = _table("DYNAMODB_TABLE_MEALS").query(
            KeyConditionExpression=Key("user_id").eq(get_user_id()) & Key("sk").between(
                f"{d}T00:00:00", f"{d}T23:59:59z"
            )
        )
        total = sum(int(item["calories"]) for item in resp["Items"])
        days.append({"date": d, "calories": total})
    return {"days": days}
