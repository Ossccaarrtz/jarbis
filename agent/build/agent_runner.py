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

    response = run_agent(user_id, text)
    telegram.send_message(chat_id, response)

    return {"statusCode": 200}
