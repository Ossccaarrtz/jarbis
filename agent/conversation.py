"""
Historial conversacional en memoria (paso 1).
En el paso 4 se reemplaza por la versión con DynamoDB,
manteniendo la misma interfaz pública.
"""

from collections import defaultdict

MAX_HISTORY = 10  # últimos N turnos (user + assistant) que se pasan a Claude

# { user_id: [{"role": "user"|"assistant", "content": str}, ...] }
_store: dict[str, list[dict]] = defaultdict(list)


def get_history(user_id: str) -> list[dict]:
    """Devuelve los últimos MAX_HISTORY mensajes del usuario."""
    return _store[user_id][-MAX_HISTORY * 2:]


def save_turn(user_id: str, user_message: str, assistant_message: str) -> None:
    """Guarda un turno completo (usuario + asistente)."""
    _store[user_id].append({"role": "user", "content": user_message})
    _store[user_id].append({"role": "assistant", "content": assistant_message})
