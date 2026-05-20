import json
from collections import defaultdict
import storage

DEFINITIONS = [
    {
        "name": "save_expense",
        "description": (
            "Guarda un gasto del usuario en la base de datos. "
            "Úsala cada vez que el usuario mencione que gastó dinero en algo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Monto numérico del gasto (ej: 15000)",
                },
                "category": {
                    "type": "string",
                    "description": (
                        "Categoría del gasto. Usa una de: comida, transporte, "
                        "entretenimiento, salud, ropa, hogar, educacion, otro"
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Descripción breve del gasto (ej: 'ramen en Sinchon')",
                },
                "currency": {
                    "type": "string",
                    "description": "Código ISO de la moneda (KRW, USD, MXN, EUR, etc.)",
                },
                "date": {
                    "type": "string",
                    "description": (
                        "Fecha del gasto en formato YYYY-MM-DD. "
                        "Úsala solo si el usuario indica una fecha distinta a hoy "
                        "(ej: 'el 8 de mayo', 'ayer', 'la semana pasada'). "
                        "Si no se menciona, omite este campo."
                    ),
                },
            },
            "required": ["amount", "category", "currency"],
        },
    },
    {
        "name": "get_expense_summary",
        "description": (
            "Obtiene un resumen de los gastos del usuario en un rango de fechas. "
            "Úsala cuando el usuario pregunte cuánto ha gastado en un período. "
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
        "name": "get_recent_expenses",
        "description": (
            "Obtiene los gastos más recientes del usuario con sus IDs. "
            "Úsala antes de eliminar un gasto para identificar cuál es."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Cantidad de gastos a retornar (default 5, máximo 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "delete_expense",
        "description": (
            "Elimina un gasto específico. "
            "Primero llama get_recent_expenses o get_expense_summary para obtener el ID. "
            "Si necesitas eliminar VARIOS gastos, usa delete_expenses_bulk en su lugar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expense_id": {
                    "type": "string",
                    "description": "ID del gasto a eliminar (campo 'id' del get_recent_expenses)",
                },
            },
            "required": ["expense_id"],
        },
    },
    {
        "name": "update_expense",
        "description": (
            "Actualiza uno o más campos de un gasto existente (monto, categoría, descripción, moneda). "
            "Úsala cuando el usuario quiera corregir un gasto registrado. "
            "Primero llama get_recent_expenses para obtener el ID del gasto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expense_id": {
                    "type": "string",
                    "description": "ID del gasto a actualizar (campo 'id' del get_recent_expenses)",
                },
                "amount": {
                    "type": "number",
                    "description": "Nuevo monto (omitir si no cambia)",
                },
                "category": {
                    "type": "string",
                    "description": "Nueva categoría (omitir si no cambia)",
                },
                "description": {
                    "type": "string",
                    "description": "Nueva descripción (omitir si no cambia)",
                },
                "currency": {
                    "type": "string",
                    "description": "Nuevo código de moneda ISO (omitir si no cambia)",
                },
            },
            "required": ["expense_id"],
        },
    },
    {
        "name": "delete_expenses_bulk",
        "description": (
            "Elimina varios gastos de una sola vez y verifica cada eliminación. "
            "Úsala cuando el usuario quiera borrar múltiples gastos. "
            "Primero llama get_expense_summary para obtener los IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expense_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de IDs de gastos a eliminar",
                },
            },
            "required": ["expense_ids"],
        },
    },
]


def _save_expense(user_id: str, inputs: dict) -> str:
    sk = storage.put_expense(
        user_id=user_id,
        amount=inputs["amount"],
        category=inputs["category"],
        description=inputs.get("description", ""),
        currency=inputs["currency"],
        date=inputs.get("date"),
    )
    # Verificar que realmente se guardó
    saved = storage.verify_expense_exists(user_id, sk)
    if saved:
        return f"Gasto guardado y verificado en base de datos (id: {sk})"
    return f"ERROR: El gasto no se pudo guardar en la base de datos. Inténtalo de nuevo."


def _get_expense_summary(user_id: str, inputs: dict) -> str:
    items = storage.query_expenses(
        user_id=user_id,
        start_date=inputs["start_date"],
        end_date=inputs["end_date"],
    )

    if not items:
        return json.dumps({
            "period": {"start": inputs["start_date"], "end": inputs["end_date"]},
            "count": 0,
            "totals_by_currency": {},
            "by_category": {},
            "transactions": [],
        })

    totals: dict[str, float] = defaultdict(float)
    by_category: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for item in items:
        cur = item["currency"]
        totals[cur] += item["amount"]
        by_category[item["category"]][cur] += item["amount"]

    return json.dumps({
        "period": {"start": inputs["start_date"], "end": inputs["end_date"]},
        "count": len(items),
        "totals_by_currency": dict(totals),
        "by_category": {cat: dict(vals) for cat, vals in by_category.items()},
        "transactions": items,
    }, ensure_ascii=False)


def _get_recent_expenses(user_id: str, inputs: dict) -> str:
    items = storage.get_recent_expenses(user_id, limit=min(inputs.get("limit", 5), 10))
    return json.dumps({"expenses": items, "count": len(items)}, ensure_ascii=False)


def _update_expense(user_id: str, inputs: dict) -> str:
    sk = inputs["expense_id"]
    fields = {k: v for k, v in inputs.items() if k != "expense_id"}
    if not fields:
        return "No se especificaron campos a actualizar."
    storage.update_expense(user_id, sk, fields)
    exists = storage.verify_expense_exists(user_id, sk)
    if exists:
        return f"Gasto {sk[:16]}... actualizado correctamente."
    return f"ERROR: No se encontró el gasto {sk[:16]}... Verifica el ID."


def _delete_expense(user_id: str, inputs: dict) -> str:
    sk = inputs["expense_id"]
    storage.delete_expense(user_id, sk)
    # Verificar que realmente se eliminó
    still_exists = storage.verify_expense_exists(user_id, sk)
    if not still_exists:
        return f"Gasto {sk[:16]}... eliminado y verificado."
    return f"ERROR: No se pudo eliminar el gasto {sk[:16]}... Inténtalo de nuevo."


def _delete_expenses_bulk(user_id: str, inputs: dict) -> str:
    """Elimina múltiples gastos de una sola vez y verifica cada uno."""
    ids = inputs["expense_ids"]
    results = []
    for sk in ids:
        storage.delete_expense(user_id, sk)
        still_exists = storage.verify_expense_exists(user_id, sk)
        if not still_exists:
            results.append(f"✓ {sk[:16]}...")
        else:
            results.append(f"✗ FALLO {sk[:16]}...")
    ok = sum(1 for r in results if r.startswith("✓"))
    return f"Eliminados {ok}/{len(ids)} gastos.\n" + "\n".join(results)


HANDLERS = {
    "save_expense": _save_expense,
    "get_expense_summary": _get_expense_summary,
    "get_recent_expenses": _get_recent_expenses,
    "update_expense": _update_expense,
    "delete_expense": _delete_expense,
    "delete_expenses_bulk": _delete_expenses_bulk,
}
