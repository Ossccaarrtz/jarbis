import os
from datetime import datetime, timezone, timedelta
import anthropic
from conversation import get_history, save_turn
from tools import TOOLS, execute_tool
import storage
import google_calendar

# Timezones reconocidos por nombre coloquial → IANA
TIMEZONE_ALIASES = {
    "korea": "Asia/Seoul",
    "corea": "Asia/Seoul",
    "seoul": "Asia/Seoul",
    "méxico": "America/Mexico_City",
    "mexico": "America/Mexico_City",
    "cdmx": "America/Mexico_City",
}

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-haiku-4-5-20251001"


def _load_user_timezone(user_id: str) -> str:
    """Carga el timezone del usuario desde preferencias y lo aplica globalmente."""
    tz_pref = storage.get_preference(user_id, "timezone")
    if tz_pref:
        iana = TIMEZONE_ALIASES.get(tz_pref.lower(), tz_pref)
        google_calendar.set_timezone(iana)
        return iana
    return "Asia/Seoul"


def _system_prompt(user_id: str) -> str:
    tz_name = _load_user_timezone(user_id)
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(tz_name))
    prefs = storage.get_all_preferences(user_id)

    prefs_text = ""
    if prefs:
        lines = "\n".join(f"  - {k}: {v}" for k, v in prefs.items())
        prefs_text = f"\nPreferencias del usuario:\n{lines}\n"

    return f"""Eres Jarbis, un asistente personal conversacional.

Fecha y hora actual: {now.strftime("%Y-%m-%d %H:%M")} (KST, hora de Corea)
Día de la semana: {["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][now.weekday()]}
{prefs_text}
REGLA CRÍTICA: SIEMPRE llama las tools para leer o escribir datos. NUNCA asumas el estado actual basándote en el historial de conversación — llama la tool cada vez sin excepción.
- Crear evento → DEBES llamar create_calendar_event
- Modificar evento → DEBES llamar list_events para obtener el ID, luego update_calendar_event
- Eliminar evento → DEBES llamar list_events para obtener el ID, luego delete_calendar_event
- Ver gastos → DEBES llamar get_expense_summary
Nunca confirmes haber ejecutado una acción sin haber llamado la tool correspondiente.

Cuando el usuario mencione gastos, comidas, eventos o recordatorios, usa las tools disponibles.
Responde siempre en el mismo idioma que el usuario (normalmente español).
Sé conciso y natural — eres un asistente personal, no un chatbot formal.
"""


def run_agent(user_id: str, user_message: str) -> str:
    """
    Ejecuta el loop agentic completo para un mensaje dado.
    Retorna el texto de respuesta final.
    """
    history = get_history(user_id)
    messages = history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=_system_prompt(user_id),
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "Listo."
            )
            save_turn(user_id, user_message, text)
            return text

        if response.stop_reason == "tool_use":
            # Puede haber múltiples tool_use en un mismo turno
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = execute_tool(user_id, block.name, block.input)
                except Exception as e:
                    print(f"[TOOL ERROR] {block.name}: {e}")
                    result = f"Error al ejecutar {block.name}: {e}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # stop_reason inesperado
        break

    return "No pude procesar tu mensaje. Intenta de nuevo."
