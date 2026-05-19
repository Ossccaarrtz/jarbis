import json
import os
import uuid
import storage
import scheduler

DEFINITIONS = [
    {
        "name": "set_reminder",
        "description": (
            "Programa un recordatorio para enviar un mensaje al usuario en una fecha y hora específica. "
            "Úsala cuando el usuario diga 'recuérdame', 'avísame', o quiera que le recuerdes algo más tarde."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Texto del recordatorio que se enviará al usuario (ej: 'Llamar a mamá')",
                },
                "remind_at": {
                    "type": "string",
                    "description": (
                        "Fecha y hora del recordatorio en formato YYYY-MM-DDTHH:MM. "
                        "Calcula la fecha exacta desde el lenguaje natural del usuario."
                    ),
                },
            },
            "required": ["message", "remind_at"],
        },
    },
    {
        "name": "list_reminders",
        "description": (
            "Lista los recordatorios pendientes del usuario. "
            "Úsala cuando el usuario pregunte qué recordatorios tiene o quiera ver sus pendientes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cancel_reminder",
        "description": (
            "Cancela un recordatorio pendiente. "
            "Primero llama list_reminders para obtener el SK del recordatorio a cancelar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_sk": {
                    "type": "string",
                    "description": "SK del recordatorio a cancelar (campo 'sk' de list_reminders)",
                },
            },
            "required": ["reminder_sk"],
        },
    },
]


def _set_reminder(user_id: str, inputs: dict) -> str:
    message = inputs["message"]
    remind_at = inputs["remind_at"]
    schedule_name = f"jarbis-{uuid.uuid4().hex[:10]}"

    sk = storage.put_reminder(
        user_id=user_id,
        message=message,
        remind_at=remind_at,
        schedule_name=schedule_name,
    )

    # Obtener timezone del usuario desde preferencias (default Asia/Seoul)
    from google_calendar import get_tz
    tz_name = get_tz().key if hasattr(get_tz(), "key") else "Asia/Seoul"
    tz_pref = storage.get_preference(user_id, "timezone")
    if tz_pref:
        from agent import TIMEZONE_ALIASES
        tz_name = TIMEZONE_ALIASES.get(tz_pref.lower(), tz_pref)

    scheduler.create_reminder_schedule(
        schedule_name=schedule_name,
        remind_at=remind_at,
        payload={
            "sk": sk,
            "user_id": user_id,
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "message": message,
        },
        timezone=tz_name,
    )

    return f"Recordatorio guardado: '{message}' para el {remind_at}"


def _list_reminders(user_id: str, inputs: dict) -> str:
    items = storage.get_pending_reminders(user_id)
    if not items:
        return json.dumps({"reminders": [], "count": 0})
    return json.dumps({"reminders": items, "count": len(items)}, ensure_ascii=False)


def _cancel_reminder(user_id: str, inputs: dict) -> str:
    sk = inputs["reminder_sk"]

    # Obtener schedule_name para eliminarlo de EventBridge
    reminders = storage.get_pending_reminders(user_id)
    reminder = next((r for r in reminders if r["sk"] == sk), None)

    if reminder and reminder.get("schedule_name"):
        scheduler.delete_reminder_schedule(reminder["schedule_name"])

    storage.delete_reminder(user_id, sk)
    return "Recordatorio cancelado."


HANDLERS = {
    "set_reminder": _set_reminder,
    "list_reminders": _list_reminders,
    "cancel_reminder": _cancel_reminder,
}
