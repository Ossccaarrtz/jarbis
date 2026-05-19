from fastapi import APIRouter, Query
from boto3.dynamodb.conditions import Key
from db import _table, _to_float, get_user_id
from datetime import date, timedelta

router = APIRouter()


def _parse_expenses(items: list) -> list:
    return [
        {
            "id": item["sk"],
            "date": item["sk"][:10],
            "amount": _to_float(item["amount"]),
            "category": item["category"],
            "description": item.get("description", ""),
            "currency": item["currency"],
        }
        for item in items
    ]


@router.get("")
def get_expenses(
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
):
    user_id = get_user_id()
    if not start_date:
        start_date = date.today().replace(day=1).isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    response = _table("DYNAMODB_TABLE_EXPENSES").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{start_date}T00:00:00",
            f"{end_date}T23:59:59z",
        )
    )
    items = _parse_expenses(response["Items"])
    total = sum(i["amount"] for i in items)
    by_category: dict = {}
    for i in items:
        by_category[i["category"]] = by_category.get(i["category"], 0) + i["amount"]

    return {
        "items": sorted(items, key=lambda x: x["date"], reverse=True),
        "total": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get("/today")
def get_today_expenses():
    today = date.today().isoformat()
    return get_expenses(start_date=today, end_date=today)


@router.get("/weekly")
def get_weekly_expenses():
    today = date.today()
    days = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        resp = _table("DYNAMODB_TABLE_EXPENSES").query(
            KeyConditionExpression=Key("user_id").eq(get_user_id()) & Key("sk").between(
                f"{d}T00:00:00", f"{d}T23:59:59z"
            )
        )
        total = sum(_to_float(item["amount"]) for item in resp["Items"])
        days.append({"date": d, "total": round(total, 2)})
    return {"days": days}
