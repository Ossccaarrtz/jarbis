"""
Lambda B — ejecuta el loop agentic completo.
Invocado de forma async por handler.py, sin presión de timeout de Telegram.
"""

import os
import telegram
from agent import run_agent


def lambda_handler(event, context):
    chat_id = event["chat_id"]
    text = event["text"]
    user_id = str(chat_id)

    try:
        response = run_agent(user_id, text)
    except Exception as e:
        print(f"[ERROR] run_agent failed: {e}")
        response = "Hubo un error procesando tu mensaje. Intenta de nuevo."

    try:
        telegram.send_message(chat_id, response)
    except Exception as e:
        print(f"[ERROR] send_message failed: {e}")

    return {"statusCode": 200}
