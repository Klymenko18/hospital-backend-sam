from __future__ import annotations

import argparse
import os

import boto3


def main() -> None:
    """
    Creates or promotes a user to Admin group.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--temp-password", default=None)
    args = parser.parse_args()

    region = os.getenv("AWS_REGION") or "eu-central-1"
    user_pool_id = os.getenv("USER_POOL_ID")
    if not user_pool_id:
        raise RuntimeError("USER_POOL_ID is required")

    client = boto3.client("cognito-idp", region_name=region)

    try:
        client.admin_get_user(UserPoolId=user_pool_id, Username=args.email)
    except client.exceptions.UserNotFoundException:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=args.email,
            TemporaryPassword=args.temp_password or "TempP@ssw0rd!",
            UserAttributes=[{"Name": "email", "Value": args.email}, {"Name": "email_verified", "Value": "true"}],
        )

    client.admin_add_user_to_group(UserPoolId=user_pool_id, Username=args.email, GroupName="Admin")


if __name__ == "__main__":
    main()
