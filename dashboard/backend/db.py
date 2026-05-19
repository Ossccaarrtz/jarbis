import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))

def _table(env_key: str):
    return dynamodb.Table(os.environ[env_key])

def _to_float(val):
    return float(val) if isinstance(val, Decimal) else val

USER_ID = os.environ.get("USER_ID", "")

def get_user_id() -> str:
    uid = os.environ.get("USER_ID", "")
    if not uid:
        raise ValueError("USER_ID not set")
    return uid
