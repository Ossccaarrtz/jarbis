"""
Tests del Lambda A (webhook handler).

Cubren la lógica de autorización: secret_token del webhook, chat_id autorizado,
y que la invocación async al Lambda B sólo ocurre cuando los chequeos pasan.
"""
import json
import os
import sys
import importlib
from unittest.mock import MagicMock


SECRET = "test-secret-token"
AUTHORIZED_CHAT = 123456


def _load_handler(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", str(AUTHORIZED_CHAT))
    monkeypatch.setenv("TELEGRAM_SECRET_TOKEN", SECRET)
    monkeypatch.setenv("AGENT_LAMBDA_NAME", "jarbis-agent-test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    # Forzar reload para que tome las env vars actuales
    if "handler" in sys.modules:
        del sys.modules["handler"]
    import handler  # noqa: F401
    importlib.reload(sys.modules["handler"])
    return sys.modules["handler"]


def _event(text="hola", chat_id=AUTHORIZED_CHAT, secret=SECRET):
    return {
        "headers": {"X-Telegram-Bot-Api-Secret-Token": secret},
        "body": json.dumps({"message": {"chat": {"id": chat_id}, "text": text}}),
    }


def test_rejects_wrong_secret_token(monkeypatch):
    handler = _load_handler(monkeypatch)
    spy = MagicMock()
    monkeypatch.setattr(handler, "lambda_client", spy)

    result = handler.lambda_handler(_event(secret="wrong"), None)
    assert result["statusCode"] == 403
    spy.invoke.assert_not_called()


def test_rejects_missing_secret_token(monkeypatch):
    handler = _load_handler(monkeypatch)
    spy = MagicMock()
    monkeypatch.setattr(handler, "lambda_client", spy)

    event = _event()
    event["headers"] = {}
    result = handler.lambda_handler(event, None)
    assert result["statusCode"] == 403
    spy.invoke.assert_not_called()


def test_ignores_unauthorized_chat_id(monkeypatch):
    handler = _load_handler(monkeypatch)
    spy = MagicMock()
    monkeypatch.setattr(handler, "lambda_client", spy)

    # Secret token correcto, pero chat_id distinto al autorizado
    result = handler.lambda_handler(_event(chat_id=999999), None)
    assert result["statusCode"] == 200
    spy.invoke.assert_not_called()


def test_ignores_empty_message(monkeypatch):
    handler = _load_handler(monkeypatch)
    spy = MagicMock()
    monkeypatch.setattr(handler, "lambda_client", spy)

    result = handler.lambda_handler(_event(text=""), None)
    assert result["statusCode"] == 200
    spy.invoke.assert_not_called()


def test_invokes_agent_async_when_authorized(monkeypatch):
    handler = _load_handler(monkeypatch)
    fake_client = MagicMock()
    fake_client.invoke.return_value = {"StatusCode": 202}
    monkeypatch.setattr(handler, "lambda_client", fake_client)

    result = handler.lambda_handler(_event(text="gasté 5000 en café"), None)
    assert result["statusCode"] == 200

    fake_client.invoke.assert_called_once()
    kwargs = fake_client.invoke.call_args.kwargs
    assert kwargs["FunctionName"] == "jarbis-agent-test"
    assert kwargs["InvocationType"] == "Event"  # async fire-and-forget

    payload = json.loads(kwargs["Payload"])
    assert payload["chat_id"] == AUTHORIZED_CHAT
    assert payload["text"] == "gasté 5000 en café"


def test_handles_edited_messages(monkeypatch):
    handler = _load_handler(monkeypatch)
    fake_client = MagicMock()
    fake_client.invoke.return_value = {"StatusCode": 202}
    monkeypatch.setattr(handler, "lambda_client", fake_client)

    event = {
        "headers": {"X-Telegram-Bot-Api-Secret-Token": SECRET},
        "body": json.dumps({
            "edited_message": {"chat": {"id": AUTHORIZED_CHAT}, "text": "edit"}
        }),
    }
    result = handler.lambda_handler(event, None)
    assert result["statusCode"] == 200
    fake_client.invoke.assert_called_once()


def test_handler_swallows_invoke_errors(monkeypatch):
    """Si falla la invocación a Lambda B, no debe propagar el error a Telegram."""
    handler = _load_handler(monkeypatch)
    fake_client = MagicMock()
    fake_client.invoke.side_effect = Exception("AWS exploded")
    monkeypatch.setattr(handler, "lambda_client", fake_client)

    result = handler.lambda_handler(_event(), None)
    # Sigue respondiendo 200 para que Telegram no reintente
    assert result["statusCode"] == 200
