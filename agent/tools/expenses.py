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
]


def _save_expense(user_id: str, inputs: dict) -> str:
    sk = storage.put_expense(
        user_id=user_id,
        amount=inputs["amount"],
        category=inputs["category"],
        description=inputs.get("description", ""),
        currency=inputs["currency"],
    )
    return f"Gasto guardado correctamente (id: {sk})"


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


HANDLERS = {
    "save_expense": _save_expense,
    "get_expense_summary": _get_expense_summary,
}
