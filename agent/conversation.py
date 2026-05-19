"""
Historial conversacional en DynamoDB (paso 4).
Misma interfaz pública que la versión en memoria del paso 1.
"""

import os
import boto3
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key

KST = timezone(timedelta(hours=9))
MAX_HISTORY = 10  # últimos N turnos (user + assistant) que se pasan a Claude

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def _table():
    return dynamodb.Table(os.environ["DYNAMODB_TABLE_CONVERSATIONS"])


def get_history(user_id: str) -> list[dict]:
    """Devuelve los últimos MAX_HISTORY mensajes en orden cronológico."""
    response = _table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,       # descendente → los más recientes primero
        Limit=MAX_HISTORY * 2,        # user + assistant por turno
    )
    items = list(reversed(response["Items"]))
    return [{"role": item["role"], "content": item["content"]} for item in items]


def save_turn(user_id: str, user_message: str, assistant_message: str) -> None:
    """Guarda un turno completo (usuario + asistente) con TTL de 24h."""
    now = datetime.now(KST)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.%f")
    expires_at = int((now + timedelta(hours=24)).timestamp())

    with _table().batch_writer() as batch:
        batch.put_item(Item={
            "user_id": user_id,
            "sk": f"{ts}#0",
            "role": "user",
            "content": user_message,
            "expires_at": expires_at,
        })
        batch.put_item(Item={
            "user_id": user_id,
            "sk": f"{ts}#1",
            "role": "assistant",
            "content": assistant_message,
            "expires_at": expires_at,
        })
