from tools.expenses import DEFINITIONS as _EXPENSE_DEFS, HANDLERS as _EXPENSE_HANDLERS
from tools.nutrition import DEFINITIONS as _NUTRITION_DEFS, HANDLERS as _NUTRITION_HANDLERS
from tools.calendar import DEFINITIONS as _CALENDAR_DEFS, HANDLERS as _CALENDAR_HANDLERS
from tools.preferences import DEFINITIONS as _PREF_DEFS, HANDLERS as _PREF_HANDLERS

TOOLS = [
    *_EXPENSE_DEFS,
    *_NUTRITION_DEFS,
    *_CALENDAR_DEFS,
    *_PREF_DEFS,
]

_handlers: dict = {
    **_EXPENSE_HANDLERS,
    **_NUTRITION_HANDLERS,
    **_CALENDAR_HANDLERS,
    **_PREF_HANDLERS,
}

# get_all_preferences disponible internamente pero no expuesto como tool del agente
# (se usa en storage directamente para el system prompt y el dashboard)


def execute_tool(user_id: str, name: str, inputs: dict) -> str:
    if name not in _handlers:
        raise NotImplementedError(f"Tool '{name}' no implementada")
    return _handlers[name](user_id, inputs)
