import os
from datetime import datetime, timezone, timedelta
import anthropic
from conversation import get_history, save_turn
from tools import TOOLS, execute_tool

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-haiku-4-5-20251001"

KST = timezone(timedelta(hours=9))


def _system_prompt() -> str:
    now = datetime.now(KST)
    return f"""Eres Jarbis, un asistente personal conversacional.

Fecha y hora actual: {now.strftime("%Y-%m-%d %H:%M")} (KST, hora de Corea)

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
            system=_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text = next(
                block.text for block in response.content
                if hasattr(block, "text")
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
