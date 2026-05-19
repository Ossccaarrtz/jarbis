from tools.expenses import DEFINITIONS as _EXPENSE_DEFS, HANDLERS as _EXPENSE_HANDLERS
from tools.nutrition import DEFINITIONS as _NUTRITION_DEFS, HANDLERS as _NUTRITION_HANDLERS

TOOLS = [
    *_EXPENSE_DEFS,
    *_NUTRITION_DEFS,
]

_handlers: dict = {
    **_EXPENSE_HANDLERS,
    **_NUTRITION_HANDLERS,
}


def execute_tool(user_id: str, name: str, inputs: dict) -> str:
    if name not in _handlers:
        raise NotImplementedError(f"Tool '{name}' no implementada")
    return _handlers[name](user_id, inputs)
