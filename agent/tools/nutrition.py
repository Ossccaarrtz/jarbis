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
]


def _log_meal(user_id: str, inputs: dict) -> str:
    sk = storage.put_meal(
        user_id=user_id,
        description=inputs["description"],
        calories=int(inputs["calories"]),
        meal_type=inputs["meal_type"],
    )
    return f"Comida registrada correctamente (id: {sk})"


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


HANDLERS = {
    "log_meal": _log_meal,
    "get_nutrition_summary": _get_nutrition_summary,
}
