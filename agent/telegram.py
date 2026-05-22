import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _url(method: str) -> str:
    return TELEGRAM_API.format(token=os.environ["TELEGRAM_BOT_TOKEN"], method=method)


def send_message(chat_id: int | str, text: str) -> None:
    """Envía un mensaje de texto al chat indicado."""
    try:
        resp = requests.post(_url("sendMessage"), json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        if not resp.ok:
            # Retry without Markdown if parse error
            if resp.status_code == 400:
                requests.post(_url("sendMessage"), json={
                    "chat_id": chat_id,
                    "text": text,
                }, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Telegram send_message failed: {e}")
        raise


def send_typing(chat_id: int | str) -> None:
    """Muestra el indicador 'escribiendo...' en Telegram. Best-effort, nunca rompe el flujo."""
    try:
        requests.post(_url("sendChatAction"), json={
            "chat_id": chat_id,
            "action": "typing",
        }, timeout=5)
    except Exception:
        pass  # Non-critical, ignore silently


def get_updates(offset: int | None = None) -> list[dict]:
    """Polling: obtiene updates nuevos desde Telegram."""
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    response = requests.get(_url("getUpdates"), params=params, timeout=35)
    response.raise_for_status()
    return response.json().get("result", [])
