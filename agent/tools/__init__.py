# Tools disponibles para el agente.
# Se agregan aquí a medida que se implementan.

TOOLS = []


def execute_tool(name: str, inputs: dict) -> str:
    raise NotImplementedError(f"Tool '{name}' no implementada")
