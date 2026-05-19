import os
import base64
import json
from fastapi import APIRouter
from datetime import datetime, timezone, timedelta

router = APIRouter()


def _get_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    raw = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS", "")
    token_data = json.loads(base64.b64decode(raw).decode())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


@router.get("")
def get_events(days_ahead: int = 7):
    service = _get_service()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=50,
    ).execute()

    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        end_time = e["end"].get("dateTime", e["end"].get("date", ""))
        events.append({
            "id": e["id"],
            "title": e.get("summary", "(Sin título)"),
            "start": start,
            "end": end_time,
            "description": e.get("description", ""),
            "location": e.get("location", ""),
            "all_day": "T" not in start,
        })

    return {"events": events, "count": len(events)}
