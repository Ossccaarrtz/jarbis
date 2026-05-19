import os
import json
import base64
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

# Timezone activo — se actualiza desde agent.py al cargar preferencias
_tz_name: str = "Asia/Seoul"


def set_timezone(iana_name: str) -> None:
    global _tz_name
    _tz_name = iana_name


def get_tz() -> ZoneInfo:
    return ZoneInfo(_tz_name)


def _get_credentials() -> Credentials:
    """Carga credenciales desde token.json (local) o env var base64 (Lambda)."""
    creds_env = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS")

    if creds_env:
        token_data = json.loads(base64.b64decode(creds_env))
    else:
        with open("token.json") as f:
            token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if not creds_env:
            with open("token.json", "w") as f:
                f.write(creds.to_json())

    return creds


def _service():
    return build("calendar", "v3", credentials=_get_credentials())


def _parse_datetime(dt_str: str) -> str:
    """Asegura que el datetime tenga segundos y timezone KST."""
    # Quitar timezone existente para normalizar
    tz_suffix = ""
    if "+" in dt_str:
        dt_str, tz_suffix = dt_str.rsplit("+", 1)
        tz_suffix = "+" + tz_suffix
    elif "Z" in dt_str:
        dt_str = dt_str.replace("Z", "")
        tz_suffix = "+00:00"

    # Asegurar que tenga segundos (HH:MM → HH:MM:00)
    time_part = dt_str.split("T")[-1] if "T" in dt_str else ""
    if time_part.count(":") == 1:
        dt_str += ":00"

    # Aplicar KST si no tenía timezone
    if not tz_suffix:
        tz_suffix = "+09:00"

    return dt_str + tz_suffix


def create_event(title: str, start_datetime: str, description: str = "",
                 end_datetime: str | None = None) -> dict:
    """
    Crea un evento en Google Calendar.
    start_datetime formato: YYYY-MM-DDTHH:MM (se asume KST si no tiene timezone).
    """
    start = _parse_datetime(start_datetime)

    if end_datetime:
        end = _parse_datetime(end_datetime)
    else:
        start_dt = datetime.fromisoformat(start)
        end = (start_dt + timedelta(hours=1)).isoformat()

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start, "timeZone": _tz_name},
        "end": {"dateTime": end, "timeZone": _tz_name},
    }

    result = _service().events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
    return {"id": result["id"], "title": result.get("summary"), "start": start}


def list_events(days_ahead: int = 7) -> list[dict]:
    """Lista eventos de los próximos N días."""
    now = datetime.now(get_tz())
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    result = _service().events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    events = []
    for item in result.get("items", []):
        start = item["start"].get("dateTime", item["start"].get("date"))
        end = item["end"].get("dateTime", item["end"].get("date"))
        events.append({
            "id": item["id"],
            "title": item.get("summary", "Sin título"),
            "start": start,
            "end": end,
            "description": item.get("description", ""),
        })

    return events


def delete_event(event_id: str) -> None:
    """Elimina un evento de Google Calendar."""
    _service().events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()


def update_event(event_id: str, title: str | None = None, start_datetime: str | None = None,
                 end_datetime: str | None = None, description: str | None = None) -> dict:
    """Actualiza un evento existente. Solo modifica los campos proporcionados."""
    existing = _service().events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()

    if title:
        existing["summary"] = title
    if description is not None:
        existing["description"] = description
    if start_datetime:
        start = _parse_datetime(start_datetime)
        existing["start"] = {"dateTime": start, "timeZone": _tz_name}
        if not end_datetime:
            start_dt = datetime.fromisoformat(start)
            end_dt = start_dt + timedelta(hours=1)
            existing["end"] = {"dateTime": end_dt.isoformat(), "timeZone": _tz_name}
    if end_datetime:
        existing["end"] = {"dateTime": _parse_datetime(end_datetime), "timeZone": _tz_name}

    result = _service().events().update(
        calendarId=CALENDAR_ID, eventId=event_id, body=existing
    ).execute()
    return {"id": result["id"], "title": result.get("summary"), "start": result["start"].get("dateTime")}
