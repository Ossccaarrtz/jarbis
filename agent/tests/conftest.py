"""
Fixtures compartidas: mockea DynamoDB con moto y configura env vars necesarias
para que `storage.py` y los tools puedan importarse y operar sin AWS real.
"""
import os
import pytest

# Env vars deben estar antes de importar boto3/storage
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")

os.environ.setdefault("DYNAMODB_TABLE_EXPENSES", "jarbis-expenses-test")
os.environ.setdefault("DYNAMODB_TABLE_MEALS", "jarbis-meals-test")
os.environ.setdefault("DYNAMODB_TABLE_REMINDERS", "jarbis-reminders-test")
os.environ.setdefault("DYNAMODB_TABLE_PREFERENCES", "jarbis-preferences-test")
os.environ.setdefault("DYNAMODB_TABLE_CONVERSATIONS", "jarbis-conversations-test")

USER_ID = "test-user"


@pytest.fixture
def aws():
    """Mockea AWS y crea las tablas de DynamoDB necesarias."""
    from moto import mock_aws
    import boto3

    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        for env_key in [
            "DYNAMODB_TABLE_EXPENSES",
            "DYNAMODB_TABLE_MEALS",
            "DYNAMODB_TABLE_REMINDERS",
            "DYNAMODB_TABLE_PREFERENCES",
            "DYNAMODB_TABLE_CONVERSATIONS",
        ]:
            client.create_table(
                TableName=os.environ[env_key],
                KeySchema=[
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    {"AttributeName": "sk", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )

        # Importar storage DESPUÉS de mock_aws para que use el cliente mockeado
        import importlib
        import storage
        importlib.reload(storage)

        yield storage


@pytest.fixture
def user_id():
    return USER_ID
