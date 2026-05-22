"""
Lambda B — ejecuta el loop agentic completo.
Invocado de forma async por handler.py, sin presión de timeout de Telegram.
"""

import os
import telegram
from agent import run_agent


def _audit_footer(tools_used: list[str]) -> str:
    if not tools_used:
        return ""
    # Mantener el orden de ejecución, mostrar repetidos.
    return "\n\n🔧 " + " · ".join(tools_used)


def lambda_handler(event, context):
    chat_id = event["chat_id"]
    text = event["text"]
    user_id = str(chat_id)

    # Mantener typing visible mientras el agente arranca.
    telegram.send_typing(chat_id)

    tools_used: list[str] = []
    try:
        response, tools_used = run_agent(user_id, text)
    except Exception as e:
        print(f"[ERROR] run_agent failed: {e}")
        response = "Hubo un error procesando tu mensaje. Intenta de nuevo."

    final = response + _audit_footer(tools_used)

    try:
        telegram.send_message(chat_id, final)
    except Exception as e:
        print(f"[ERROR] send_message failed: {e}")

    return {"statusCode": 200}
