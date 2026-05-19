"""
Lambda A — entry point del webhook de Telegram.
Responde 200 inmediatamente y delega el procesamiento a Lambda B (async).
"""

import json
import os
import boto3

lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION", "us-east-1"))

AUTHORIZED_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
SECRET_TOKEN = os.environ.get("TELEGRAM_SECRET_TOKEN", "")
AGENT_LAMBDA_NAME = os.environ["AGENT_LAMBDA_NAME"]

_OK = {"statusCode": 200, "body": "ok"}


def lambda_handler(event, context):
    # Validar secret token del webhook
    if SECRET_TOKEN:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        if headers.get("x-telegram-bot-api-secret-token") != SECRET_TOKEN:
            return {"statusCode": 403, "body": "Forbidden"}

    body = json.loads(event.get("body") or "{}")
    message = body.get("message") or body.get("edited_message")

    if not message:
        return _OK

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id != AUTHORIZED_CHAT_ID or not text:
        return _OK

    # Invocar Lambda B de forma async (InvocationType=Event = fire and forget)
    lambda_client.invoke(
        FunctionName=AGENT_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps({"chat_id": chat_id, "text": text}),
    )

    return _OK
