from __future__ import annotations

import argparse
import csv
import os
import random
import string
from typing import List

import boto3
from faker import Faker


def _temp_password() -> str:
    """
    Generates a temporary password satisfying Cognito defaults.
    """
    letters = string.ascii_letters
    digits = string.digits
    base = "".join(random.choice(letters) for _ in range(8))
    base += random.choice(digits)
    base += "!"
    return base


def main() -> None:
    """
    Creates N fake patient users in Cognito and writes CSV with email, temporary_password, sub.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--out", type=str, default="out/patients.csv")
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN", "false") == "true")
    args = parser.parse_args()

    region = os.getenv("AWS_REGION") or "eu-central-1"
    user_pool_id = os.getenv("USER_POOL_ID")
    if not user_pool_id:
        raise RuntimeError("USER_POOL_ID is required")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    client = boto3.client("cognito-idp", region_name=region)
    fake = Faker()

    rows: List[List[str]] = []
    for _ in range(args.count):
        email = fake.unique.email()
        temp_pwd = _temp_password()
        if not args.dry_run:
            client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                TemporaryPassword=temp_pwd,
                UserAttributes=[{"Name": "email", "Value": email}, {"Name": "email_verified", "Value": "true"}],
                DesiredDeliveryMediums=["EMAIL"],
            )
            user = client.admin_get_user(UserPoolId=user_pool_id, Username=email)
            sub = next((a["Value"] for a in user["UserAttributes"] if a["Name"] == "sub"), None)
            client.admin_add_user_to_group(UserPoolId=user_pool_id, Username=email, GroupName="Patients")
        else:
            sub = f"dry-{fake.uuid4()}"
        rows.append([email, temp_pwd, sub or ""])

    with open(args.out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "temporary_password", "sub"])
        writer.writerows(rows)


if __name__ == "__main__":
    main()
