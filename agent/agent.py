import os
from datetime import datetime, timezone, timedelta
import anthropic
from conversation import get_history, save_turn
from tools import TOOLS, execute_tool
import storage
import google_calendar
import telegram

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

    weekday_es = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][now.weekday()]
    return f"""You are Jarbis, a personal conversational assistant.

Current date/time: {now.strftime("%Y-%m-%d %H:%M")} ({tz_name})
Day of week: {weekday_es}
{prefs_text}
LANGUAGE — match the user's language EXACTLY in every reply.
- User writes English → reply English.
- User writes Spanish → reply Spanish.
- Never default to Spanish if the user wrote in another language.

CONVERSATION vs ACTION:
- Greetings, thanks, clarifications, small talk → just chat. Do NOT call any tool.
- Only call tools when the user actually asks to record / query / modify / delete data,
  or when you need a real value (date, ID, current balance) that only a tool can give.

ANTI-HALLUCINATION — CRITICAL:
- Never claim you did something unless you called the corresponding tool in THIS turn and
  it returned a success string. No "✅ done" without a real tool_result.
- Quote the tool result text. Do NOT invent IDs, amounts, dates, calorie numbers or counts.
- If a tool returns ERROR / "NO EXISTE" / "no se pudo", tell the user exactly that.
  Never paper over a tool failure with an optimistic confirmation.
- Do NOT re-execute a write you already did in a previous turn just because the user asked
  "¿lo hiciste?" — instead call the matching get_* tool and report the actual state.
- For destructive bulk operations (>3 items), list what you'll delete and ask for explicit
  confirmation before calling delete_*_bulk.

Be concise and natural — you're a personal assistant, not a formal chatbot.
"""


def run_agent(user_id: str, user_message: str) -> tuple[str, list[str]]:
    """
    Ejecuta el loop agentic completo para un mensaje dado.
    Retorna (texto_respuesta, lista_de_tools_ejecutadas).
    """
    history = get_history(user_id)
    messages = history + [{"role": "user", "content": user_message}]
    tools_called = 0
    tools_used: list[str] = []
    nudged = False

    # chat_id == user_id como string para el caso de Telegram.
    try:
        chat_id_int = int(user_id)
    except (TypeError, ValueError):
        chat_id_int = None

    while True:
        if chat_id_int is not None:
            telegram.send_typing(chat_id_int)

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
            # Suave: si la respuesta luce como una confirmación pero no se llamó ninguna tool,
            # recordamos una sola vez. NO forzamos cuando hubo lookups: una consulta puede
            # ser la respuesta completa y correcta (y forzar escrituras ahí fue lo que
            # corrompió datos antes).
            looks_like_confirmation = (
                "✓" in text or "✅" in text
                or "listo" in text.lower() or "hecho" in text.lower()
                or "registrado" in text.lower() or "guardado" in text.lower()
                or "eliminad" in text.lower() or "actualizad" in text.lower()
            )
            if tools_called == 0 and looks_like_confirmation and not nudged:
                print("[WARNING] confirmación sin tool_use — recordando una vez")
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{
                    "type": "text",
                    "text": (
                        "Tu respuesta afirma que ejecutaste una acción, pero no llamaste "
                        "ninguna tool. Si la acción es real, llama la tool ahora. Si fue "
                        "solo conversación (saludo, agradecimiento, aclaración), responde "
                        "normal sin afirmar haber hecho nada."
                    ),
                }]})
                nudged = True
                continue
            save_turn(user_id, user_message, text)
            return text, tools_used

        if response.stop_reason == "tool_use":
            tools_called += 1
            # Puede haber múltiples tool_use en un mismo turno
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"[TOOL CALL] {block.name} | input: {block.input}")
                tools_used.append(block.name)
                try:
                    result = execute_tool(user_id, block.name, block.input)
                    print(f"[TOOL RESULT] {block.name} | result: {str(result)[:200]}")
                except Exception as e:
                    print(f"[TOOL ERROR] {block.name}: {e}")
                    result = f"Error al ejecutar {block.name}: {e}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_results})
            # Reset nudged: si ya llamó una tool, el ciclo de confirmación queda saldado.
            nudged = False
            continue

        # stop_reason inesperado
        break

    return "No pude procesar tu mensaje. Intenta de nuevo.", tools_used
