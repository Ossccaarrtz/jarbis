import json
import storage

DEFINITIONS = [
    {
        "name": "save_preference",
        "description": (
            "Guarda una preferencia o configuración personal del usuario de forma permanente. "
            "Úsala cuando el usuario defina límites, metas o configuraciones que quiera recordar "
            "entre conversaciones (presupuesto semanal, meta calórica diaria, etc.).\n\n"
            "Claves estándar a usar:\n"
            "- budget_weekly_KRW, budget_weekly_USD, budget_monthly_KRW, etc. → presupuesto por período y moneda\n"
            "- calorie_goal_daily → meta de calorías diarias\n"
            "- timezone → zona horaria del usuario (valores: 'Asia/Seoul', 'America/Mexico_City', etc.)\n"
            "  Úsala cuando el usuario diga 'estoy en México', 'estoy en Korea', o cambie de país.\n"
            "- Para otras preferencias, usa snake_case descriptivo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Clave de la preferencia (ej: 'budget_weekly_KRW', 'calorie_goal_daily')",
                },
                "value": {
                    "type": "string",
                    "description": "Valor de la preferencia (siempre como string, ej: '80000', '2000')",
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "get_preference",
        "description": (
            "Obtiene una preferencia guardada del usuario. "
            "Úsala cuando necesites saber el presupuesto configurado, la meta calórica, u otra preferencia."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Clave de la preferencia a obtener",
                },
            },
            "required": ["key"],
        },
    },
]


def _save_preference(user_id: str, inputs: dict) -> str:
    storage.put_preference(user_id, inputs["key"], inputs["value"])
    return f"Preferencia guardada: {inputs['key']} = {inputs['value']}"


def _get_preference(user_id: str, inputs: dict) -> str:
    value = storage.get_preference(user_id, inputs["key"])
    if value is None:
        return json.dumps({"key": inputs["key"], "value": None, "found": False})
    return json.dumps({"key": inputs["key"], "value": value, "found": True})


def _get_all_preferences(user_id: str, inputs: dict) -> str:
    prefs = storage.get_all_preferences(user_id)
    return json.dumps({"preferences": prefs, "count": len(prefs)}, ensure_ascii=False)


HANDLERS = {
    "save_preference": _save_preference,
    "get_preference": _get_preference,
    "get_all_preferences": _get_all_preferences,
}
