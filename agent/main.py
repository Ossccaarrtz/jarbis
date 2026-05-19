"""
Punto de entrada para desarrollo local — modo polling.
Uso: python main.py

En producción se reemplaza por Lambda + API Gateway (webhook).
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

import telegram
from agent import run_agent

AUTHORIZED_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])


def process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id != AUTHORIZED_CHAT_ID:
        print(f"[BLOCKED] chat_id no autorizado: {chat_id}")
        return

    if not text:
        return

    user_id = str(chat_id)
    print(f"[IN]  {text}")

    response = run_agent(user_id, text)

    print(f"[OUT] {response}")
    telegram.send_message(chat_id, response)


def main() -> None:
    print("Jarbis corriendo en modo polling...")
    offset = None

    while True:
        try:
            updates = telegram.get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                process_update(update)
        except KeyboardInterrupt:
            print("\nDetenido.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
