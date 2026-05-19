"""
Lambda C — dispatcher de recordatorios.
Invocado por EventBridge Scheduler en la fecha/hora programada.
Envía el mensaje al usuario por Telegram y marca el reminder como enviado.
"""

import os
import telegram
import storage


def lambda_handler(event, context):
    sk = event.get("sk")
    user_id = event.get("user_id")
    chat_id = event["chat_id"]
    message = event["message"]

    telegram.send_message(chat_id, f"⏰ *Recordatorio:* {message}")

    if sk and user_id:
        storage.mark_reminder_sent(user_id, sk)

    return {"statusCode": 200}
