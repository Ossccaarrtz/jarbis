import json
from collections import defaultdict
import storage

DEFINITIONS = [
    {
        "name": "log_meal",
        "description": (
            "Registra una comida del usuario. "
            "Úsala cuando el usuario mencione que comió, desayunó, almorzó, cenó, o tuvo un snack."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Descripción de lo que comió (ej: 'avena con fruta y miel')",
                },
                "calories": {
                    "type": "integer",
                    "description": (
                        "Calorías estimadas. Si el usuario no las menciona, estímalas tú "
                        "basándote en la comida descrita."
                    ),
                },
                "meal_type": {
                    "type": "string",
                    "description": "Tipo de comida: desayuno, almuerzo, cena, snack",
                },
                "date": {
                    "type": "string",
                    "description": (
                        "Fecha de la comida en formato YYYY-MM-DD. "
                        "Úsala solo si el usuario indica una fecha distinta a hoy. "
                        "Si no se menciona, omite este campo."
                    ),
                },
            },
            "required": ["description", "calories", "meal_type"],
        },
    },
    {
        "name": "get_nutrition_summary",
        "description": (
            "Obtiene un resumen de las comidas y calorías del usuario en un rango de fechas. "
            "Úsala cuando el usuario pregunte cómo va con su alimentación o cuántas calorías consumió. "
            "Las fechas deben estar en formato YYYY-MM-DD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Fecha inicio (YYYY-MM-DD), inclusive",
                },
                "end_date": {
                    "type": "string",
                    "description": "Fecha fin (YYYY-MM-DD), inclusive",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "get_recent_meals",
        "description": (
            "Obtiene las comidas más recientes del usuario con sus IDs. "
            "Úsala antes de eliminar una comida para identificar cuál es."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Cantidad de comidas a retornar (default 5, máximo 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "delete_meal",
        "description": (
            "Elimina una comida registrada. "
            "Primero llama get_recent_meals para obtener el ID de la comida a eliminar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_id": {
                    "type": "string",
                    "description": "ID de la comida a eliminar (campo 'id' del get_recent_meals)",
                },
            },
            "required": ["meal_id"],
        },
    },
]


def _log_meal(user_id: str, inputs: dict) -> str:
    sk = storage.put_meal(
        user_id=user_id,
        description=inputs["description"],
        calories=int(inputs["calories"]),
        meal_type=inputs["meal_type"],
        date=inputs.get("date"),
    )
    saved = storage.verify_meal_exists(user_id, sk)
    if saved:
        return f"Comida registrada y verificada en base de datos (id: {sk})"
    return "ERROR: La comida no se pudo guardar en la base de datos. Inténtalo de nuevo."


def _get_nutrition_summary(user_id: str, inputs: dict) -> str:
    items = storage.query_meals(
        user_id=user_id,
        start_date=inputs["start_date"],
        end_date=inputs["end_date"],
    )

    if not items:
        return json.dumps({
            "period": {"start": inputs["start_date"], "end": inputs["end_date"]},
            "count": 0,
            "total_calories": 0,
            "by_meal_type": {},
            "meals": [],
        })

    total_calories = sum(item["calories"] for item in items)
    by_meal_type: dict[str, dict] = defaultdict(lambda: {"calories": 0, "count": 0})

    for item in items:
        by_meal_type[item["meal_type"]]["calories"] += item["calories"]
        by_meal_type[item["meal_type"]]["count"] += 1

    return json.dumps({
        "period": {"start": inputs["start_date"], "end": inputs["end_date"]},
        "count": len(items),
        "total_calories": total_calories,
        "by_meal_type": {k: dict(v) for k, v in by_meal_type.items()},
        "meals": items,
    }, ensure_ascii=False)


def _get_recent_meals(user_id: str, inputs: dict) -> str:
    items = storage.get_recent_meals(user_id, limit=min(inputs.get("limit", 5), 10))
    return json.dumps({"meals": items, "count": len(items)}, ensure_ascii=False)


def _delete_meal(user_id: str, inputs: dict) -> str:
    sk = inputs["meal_id"]
    storage.delete_meal(user_id, sk)
    still_exists = storage.verify_meal_exists(user_id, sk)
    if not still_exists:
        return f"Comida {sk[:16]}... eliminada y verificada."
    return f"ERROR: No se pudo eliminar la comida {sk[:16]}... Inténtalo de nuevo."


HANDLERS = {
    "log_meal": _log_meal,
    "get_nutrition_summary": _get_nutrition_summary,
    "get_recent_meals": _get_recent_meals,
    "delete_meal": _delete_meal,
}
