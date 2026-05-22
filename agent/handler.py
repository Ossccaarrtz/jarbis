"""
Lambda A — entry point del webhook de Telegram.
Responde 200 inmediatamente y delega el procesamiento a Lambda B (async).
"""

import json
import os
import boto3
import telegram

lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION", "us-east-1"))

AUTHORIZED_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
SECRET_TOKEN = os.environ["TELEGRAM_SECRET_TOKEN"]  # Requerido — falla en startup si falta
AGENT_LAMBDA_NAME = os.environ["AGENT_LAMBDA_NAME"]

_OK = {"statusCode": 200, "body": "ok"}


def lambda_handler(event, context):
    # Validar secret token del webhook — siempre requerido
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

    # Typing inmediato — visible mientras Lambda B arranca (~1-3s).
    telegram.send_typing(chat_id)

    # Invocar Lambda B de forma async (InvocationType=Event = fire and forget)
    try:
        resp = lambda_client.invoke(
            FunctionName=AGENT_LAMBDA_NAME,
            InvocationType="Event",
            Payload=json.dumps({"chat_id": chat_id, "text": text}),
        )
        if resp.get("StatusCode") != 202:
            print(f"[ERROR] Lambda invoke returned unexpected status: {resp.get('StatusCode')}")
    except Exception as e:
        print(f"[ERROR] Failed to invoke agent Lambda: {e}")

    return _OK
