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
            "Primero llama get_recent_meals para obtener el ID. "
            "Si necesitas eliminar VARIAS comidas, usa delete_meals_bulk."
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
    {
        "name": "update_meal",
        "description": (
            "Actualiza uno o más campos de una comida registrada (descripción, calorías, tipo). "
            "Úsala cuando el usuario quiera corregir una comida. "
            "Primero llama get_recent_meals para obtener el ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_id": {
                    "type": "string",
                    "description": "ID de la comida a actualizar (campo 'id' del get_recent_meals)",
                },
                "description": {
                    "type": "string",
                    "description": "Nueva descripción (omitir si no cambia)",
                },
                "calories": {
                    "type": "integer",
                    "description": "Nuevas calorías estimadas (omitir si no cambia)",
                },
                "meal_type": {
                    "type": "string",
                    "description": "Nuevo tipo de comida: desayuno, almuerzo, cena, snack (omitir si no cambia)",
                },
            },
            "required": ["meal_id"],
        },
    },
    {
        "name": "delete_meals_bulk",
        "description": (
            "Elimina varias comidas de una sola vez y verifica cada eliminación. "
            "Úsala cuando el usuario quiera borrar múltiples comidas. "
            "Primero llama get_nutrition_summary o get_recent_meals para obtener los IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de IDs de comidas a eliminar",
                },
            },
            "required": ["meal_ids"],
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


_MEAL_UPDATABLE = {"description", "calories", "meal_type"}


def _update_meal(user_id: str, inputs: dict) -> str:
    sk = inputs["meal_id"]
    raw = {k: v for k, v in inputs.items() if k != "meal_id"}
    invalid = sorted(set(raw) - _MEAL_UPDATABLE)
    fields = {k: v for k, v in raw.items() if k in _MEAL_UPDATABLE}

    if not fields:
        if invalid:
            return (
                f"ERROR: Los campos {invalid} no son editables. "
                f"Solo se pueden actualizar: {sorted(_MEAL_UPDATABLE)}. "
                "Para cambiar la fecha, elimina la comida y créala de nuevo con la fecha correcta."
            )
        return "No se especificaron campos a actualizar."

    if not storage.verify_meal_exists(user_id, sk):
        return f"ERROR: No existe ninguna comida con ID {sk[:16]}... Verifica con get_recent_meals."

    storage.update_meal(user_id, sk, fields)

    if invalid:
        return (
            f"Comida {sk[:16]}... actualizada parcialmente. "
            f"Ignorados (no editables): {invalid}. "
            "Para cambiar la fecha, elimina y recrea."
        )
    return f"Comida {sk[:16]}... actualizada correctamente."


def _delete_meal(user_id: str, inputs: dict) -> str:
    sk = inputs["meal_id"]
    if not storage.verify_meal_exists(user_id, sk):
        return f"ERROR: No existe ninguna comida con ID {sk[:16]}... Verifica con get_recent_meals."
    storage.delete_meal(user_id, sk)
    if storage.verify_meal_exists(user_id, sk):
        return f"ERROR: No se pudo eliminar la comida {sk[:16]}... Inténtalo de nuevo."
    return f"Comida {sk[:16]}... eliminada y verificada."


def _delete_meals_bulk(user_id: str, inputs: dict) -> str:
    """Elimina múltiples comidas. Cuenta como éxito solo si el item existía y dejó de existir."""
    ids = inputs["meal_ids"]
    results = []
    ok = 0
    for sk in ids:
        if not storage.verify_meal_exists(user_id, sk):
            results.append(f"✗ NO EXISTE {sk[:16]}...")
            continue
        storage.delete_meal(user_id, sk)
        if storage.verify_meal_exists(user_id, sk):
            results.append(f"✗ FALLO {sk[:16]}...")
        else:
            results.append(f"✓ {sk[:16]}...")
            ok += 1
    return f"Eliminadas {ok}/{len(ids)} comidas.\n" + "\n".join(results)


HANDLERS = {
    "log_meal": _log_meal,
    "get_nutrition_summary": _get_nutrition_summary,
    "get_recent_meals": _get_recent_meals,
    "update_meal": _update_meal,
    "delete_meal": _delete_meal,
    "delete_meals_bulk": _delete_meals_bulk,
}
