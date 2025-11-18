"""Seed Cognito users: N patients + 1 admin, capture their subs."""

from __future__ import annotations

import os
import random
import string
from typing import Dict, List

import boto3


def _rand_pwd(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def run(count: int = 5) -> Dict[str, str]:
    pool_id = os.environ["USER_POOL_ID"]
    client = boto3.client("cognito-idp")

    created: Dict[str, str] = {}
    # Admin
    admin_email = "admin@example.com"
    admin_pwd = _rand_pwd()
    client.admin_create_user(
        UserPoolId=pool_id, Username=admin_email, UserAttributes=[{"Name": "email", "Value": admin_email}]
    )
    client.admin_set_user_password(
        UserPoolId=pool_id, Username=admin_email, Password=admin_pwd, Permanent=True
    )
    client.admin_add_user_to_group(UserPoolId=pool_id, Username=admin_email, GroupName="admin")
    admin = client.admin_get_user(UserPoolId=pool_id, Username=admin_email)
    admin_sub = next(a["Value"] for a in admin["UserAttributes"] if a["Name"] == "sub")
    created[admin_email] = admin_sub

    # Patients
    for i in range(count):
        email = f"patient{i+1}@example.com"
        pwd = _rand_pwd()
        client.admin_create_user(
            UserPoolId=pool_id, Username=email, UserAttributes=[{"Name": "email", "Value": email}]
        )
        client.admin_set_user_password(UserPoolId=pool_id, Username=email, Password=pwd, Permanent=True)
        client.admin_add_user_to_group(UserPoolId=pool_id, Username=email, GroupName="patients")
        u = client.admin_get_user(UserPoolId=pool_id, Username=email)
        sub = next(a["Value"] for a in u["UserAttributes"] if a["Name"] == "sub")
        created[email] = sub

    return created


if __name__ == "__main__":
    users = run(count=int(os.getenv("SEED_COUNT", "5")))
    print(users)
