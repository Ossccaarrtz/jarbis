from fastapi import APIRouter
from boto3.dynamodb.conditions import Key, Attr
from db import _table, get_user_id

router = APIRouter()


@router.get("")
def get_reminders():
    user_id = get_user_id()
    response = _table("DYNAMODB_TABLE_REMINDERS").query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("sent").eq(False),
    )
    items = [
        {
            "sk": item["sk"],
            "message": item["message"],
            "remind_at": item.get("remind_at", ""),
        }
        for item in response["Items"]
    ]
    items.sort(key=lambda x: x["remind_at"])
    return {"reminders": items, "count": len(items)}
