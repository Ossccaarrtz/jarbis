import json
import google_calendar

DEFINITIONS = [
    {
        "name": "create_calendar_event",
        "description": (
            "Crea un evento en Google Calendar del usuario. "
            "Úsala cuando el usuario quiera agendar algo, crear un recordatorio en el calendario, "
            "o registrar una cita, reunión o evento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Título del evento (ej: 'Llamar a mamá', 'Gym', 'Dentista')",
                },
                "start_datetime": {
                    "type": "string",
                    "description": (
                        "Fecha y hora de inicio en formato YYYY-MM-DDTHH:MM. "
                        "Calcula la fecha exacta a partir de lo que diga el usuario "
                        "(ej: 'mañana a las 7pm' → '2026-05-20T19:00'). "
                        "Se asume hora de Corea (KST)."
                    ),
                },
                "end_datetime": {
                    "type": "string",
                    "description": (
                        "Fecha y hora de fin en formato YYYY-MM-DDTHH:MM. "
                        "Si el usuario no la menciona, omite este campo (se usará 1 hora después del inicio)."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Descripción o notas adicionales del evento (opcional).",
                },
            },
            "required": ["title", "start_datetime"],
        },
    },
    {
        "name": "list_events",
        "description": (
            "Lista los próximos eventos del Google Calendar del usuario. "
            "Úsala cuando el usuario pregunte qué tiene pendiente, qué hay en su agenda, "
            "o qué eventos tiene en los próximos días."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": (
                        "Cuántos días hacia adelante buscar. "
                        "Ejemplos: 1 = solo hoy, 7 = próxima semana, 30 = próximo mes."
                    ),
                },
            },
            "required": ["days_ahead"],
        },
    },
]


def _create_calendar_event(user_id: str, inputs: dict) -> str:
    result = google_calendar.create_event(
        title=inputs["title"],
        start_datetime=inputs["start_datetime"],
        description=inputs.get("description", ""),
        end_datetime=inputs.get("end_datetime"),
    )
    event_id = result["id"]
    verified = google_calendar.get_event(event_id)
    if verified:
        return f"Evento creado y verificado en Google Calendar: {result['title']} el {result['start']} (id: {event_id})"
    return f"ERROR: El evento no se pudo verificar en Google Calendar. Inténtalo de nuevo."


def _list_events(user_id: str, inputs: dict) -> str:
    events = google_calendar.list_events(days_ahead=inputs["days_ahead"])
    if not events:
        return json.dumps({"events": [], "count": 0})
    return json.dumps({"events": events, "count": len(events)}, ensure_ascii=False)


DEFINITIONS.append({
    "name": "delete_calendar_event",
    "description": (
        "Elimina un evento de Google Calendar. "
        "Úsala cuando el usuario quiera cancelar o borrar un evento, "
        "o cuando un update no funcionó y es más fácil borrar y recrear. "
        "Primero llama list_events para obtener el ID del evento."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "ID del evento a eliminar (campo 'id' del list_events)",
            },
        },
        "required": ["event_id"],
    },
})

DEFINITIONS.append({
    "name": "update_calendar_event",
    "description": (
        "Modifica un evento existente en Google Calendar. "
        "Úsala cuando el usuario quiera cambiar la fecha, hora, título o descripción de un evento. "
        "Primero llama list_events para obtener el ID del evento."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "ID del evento a modificar (campo 'id' del list_events)",
            },
            "title": {
                "type": "string",
                "description": "Nuevo título del evento (omitir si no cambia)",
            },
            "start_datetime": {
                "type": "string",
                "description": "Nueva fecha y hora de inicio YYYY-MM-DDTHH:MM (omitir si no cambia)",
            },
            "end_datetime": {
                "type": "string",
                "description": "Nueva fecha y hora de fin YYYY-MM-DDTHH:MM (omitir si no cambia)",
            },
            "description": {
                "type": "string",
                "description": "Nueva descripción del evento (omitir si no cambia)",
            },
        },
        "required": ["event_id"],
    },
})


def _update_calendar_event(user_id: str, inputs: dict) -> str:
    result = google_calendar.update_event(
        event_id=inputs["event_id"],
        title=inputs.get("title"),
        start_datetime=inputs.get("start_datetime"),
        end_datetime=inputs.get("end_datetime"),
        description=inputs.get("description"),
    )
    return f"Evento actualizado: {result['title']} — {result['start']}"


def _delete_calendar_event(user_id: str, inputs: dict) -> str:
    google_calendar.delete_event(inputs["event_id"])
    return "Evento eliminado correctamente."


HANDLERS = {
    "create_calendar_event": _create_calendar_event,
    "list_events": _list_events,
    "update_calendar_event": _update_calendar_event,
    "delete_calendar_event": _delete_calendar_event,
}
