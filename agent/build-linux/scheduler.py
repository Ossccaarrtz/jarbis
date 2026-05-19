"""
Operaciones con EventBridge Scheduler para recordatorios one-shot.
Si las vars de entorno no están configuradas (desarrollo local), las operaciones son no-op.
"""

import json
import os
import boto3

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("scheduler", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return _client


def _is_configured() -> bool:
    return bool(
        os.environ.get("REMINDER_DISPATCHER_LAMBDA_ARN")
        and os.environ.get("EVENTBRIDGE_SCHEDULER_ROLE_ARN")
    )


def _normalize_datetime(dt_str: str) -> str:
    """Asegura formato YYYY-MM-DDTHH:MM:SS requerido por EventBridge at()."""
    if "T" not in dt_str:
        dt_str += "T00:00:00"
    parts = dt_str.split("T")
    time_part = parts[1].split("+")[0].split("Z")[0]
    if time_part.count(":") == 1:
        time_part += ":00"
    return f"{parts[0]}T{time_part}"


def create_reminder_schedule(schedule_name: str, remind_at: str,
                              payload: dict, timezone: str = "Asia/Seoul") -> None:
    if not _is_configured():
        print(f"[SCHEDULER] Skipped (local dev) — schedule: {schedule_name} at {remind_at}")
        return

    _get_client().create_schedule(
        Name=schedule_name,
        ScheduleExpression=f"at({_normalize_datetime(remind_at)})",
        ScheduleExpressionTimezone=timezone,
        FlexibleTimeWindow={"Mode": "OFF"},
        Target={
            "Arn": os.environ["REMINDER_DISPATCHER_LAMBDA_ARN"],
            "RoleArn": os.environ["EVENTBRIDGE_SCHEDULER_ROLE_ARN"],
            "Input": json.dumps(payload),
        },
        ActionAfterCompletion="DELETE",
    )


def delete_reminder_schedule(schedule_name: str) -> None:
    if not _is_configured():
        return
    try:
        _get_client().delete_schedule(Name=schedule_name)
    except Exception:
        pass  # Ya fue disparado y auto-eliminado, o nunca se creó
