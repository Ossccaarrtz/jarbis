import os
import uuid
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key

KST = timezone(timedelta(hours=9))

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _table(name_env: str):
    return dynamodb.Table(os.environ[name_env])


def _now_kst() -> datetime:
    return datetime.now(KST)


def _ttl_1year(from_dt: datetime) -> int:
    return int((from_dt + timedelta(days=365)).timestamp())


def _to_float(val):
    """Convierte Decimal de DynamoDB a float."""
    return float(val) if isinstance(val, Decimal) else val


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


def put_expense(user_id: str, amount: float, category: str,
                description: str, currency: str, date: str | None = None) -> str:
    now = _now_kst()
    if date:
        sk = f"{date}T00:00:00#{uuid.uuid4()}"
    else:
        sk = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}#{uuid.uuid4()}"

    _table("DYNAMODB_TABLE_EXPENSES").put_item(Item={
        "user_id": user_id,
        "sk": sk,
        "amount": Decimal(str(amount)),
        "category": category.lower(),
        "description": description or "",
        "currency": currency.upper(),
        "expires_at": _ttl_1year(now),
    })
    return sk


def query_expenses(user_id: str, start_date: str, end_date: str) -> list[dict]:
    """
    Retorna gastos entre start_date y end_date (formato YYYY-MM-DD, inclusive).
    """
    response = _table("DYNAMODB_TABLE_EXPENSES").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{start_date}T00:00:00",
            f"{end_date}T23:59:59z",  # 'z' > cualquier dígito o '#'
        )
    )
    return [
        {
            "date": item["sk"][:10],
            "amount": _to_float(item["amount"]),
            "category": item["category"],
            "description": item.get("description", ""),
            "currency": item["currency"],
        }
        for item in response["Items"]
    ]


def get_recent_expenses(user_id: str, limit: int = 5) -> list[dict]:
    """Retorna los N gastos más recientes con su ID (sk) para poder eliminarlos."""
    response = _table("DYNAMODB_TABLE_EXPENSES").query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [
        {
            "id": item["sk"],
            "date": item["sk"][:10],
            "amount": _to_float(item["amount"]),
            "category": item["category"],
            "description": item.get("description", ""),
            "currency": item["currency"],
        }
        for item in response["Items"]
    ]


def delete_expense(user_id: str, sk: str) -> None:
    _table("DYNAMODB_TABLE_EXPENSES").delete_item(
        Key={"user_id": user_id, "sk": sk}
    )


# ---------------------------------------------------------------------------
# Meals
# ---------------------------------------------------------------------------

def put_meal(user_id: str, description: str, calories: int, meal_type: str,
             date: str | None = None) -> str:
    now = _now_kst()
    if date:
        sk = f"{date}T00:00:00#{uuid.uuid4()}"
    else:
        sk = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}#{uuid.uuid4()}"

    _table("DYNAMODB_TABLE_MEALS").put_item(Item={
        "user_id": user_id,
        "sk": sk,
        "description": description,
        "calories": calories,
        "meal_type": meal_type.lower(),
        "expires_at": _ttl_1year(now),
    })
    return sk


def query_meals(user_id: str, start_date: str, end_date: str) -> list[dict]:
    response = _table("DYNAMODB_TABLE_MEALS").query(
        KeyConditionExpression=Key("user_id").eq(user_id) & Key("sk").between(
            f"{start_date}T00:00:00",
            f"{end_date}T23:59:59z",
        )
    )
    return [
        {
            "date": item["sk"][:10],
            "time": item["sk"][11:16],
            "description": item["description"],
            "calories": int(item["calories"]),
            "meal_type": item["meal_type"],
        }
        for item in response["Items"]
    ]


def get_recent_meals(user_id: str, limit: int = 5) -> list[dict]:
    """Retorna las N comidas más recientes con su ID (sk) para poder eliminarlas."""
    response = _table("DYNAMODB_TABLE_MEALS").query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [
        {
            "id": item["sk"],
            "date": item["sk"][:10],
            "description": item["description"],
            "calories": int(item["calories"]),
            "meal_type": item["meal_type"],
        }
        for item in response["Items"]
    ]


def delete_meal(user_id: str, sk: str) -> None:
    _table("DYNAMODB_TABLE_MEALS").delete_item(
        Key={"user_id": user_id, "sk": sk}
    )


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

def put_preference(user_id: str, key: str, value: str) -> None:
    _table("DYNAMODB_TABLE_PREFERENCES").put_item(Item={
        "user_id": user_id,
        "sk": key,
        "value": value,
    })


def get_preference(user_id: str, key: str) -> str | None:
    response = _table("DYNAMODB_TABLE_PREFERENCES").get_item(
        Key={"user_id": user_id, "sk": key}
    )
    item = response.get("Item")
    return item["value"] if item else None


def get_all_preferences(user_id: str) -> dict[str, str]:
    response = _table("DYNAMODB_TABLE_PREFERENCES").query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    return {item["sk"]: item["value"] for item in response["Items"]}
