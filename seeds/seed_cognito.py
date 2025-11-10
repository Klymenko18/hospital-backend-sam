from __future__ import annotations

import argparse
from typing import List, Tuple

import boto3


def ensure_group(cognito, user_pool_id: str, group_name: str) -> None:
    """Create the group if it does not exist."""
    try:
        cognito.get_group(UserPoolId=user_pool_id, GroupName=group_name)
    except cognito.exceptions.ResourceNotFoundException:
        cognito.create_group(UserPoolId=user_pool_id, GroupName=group_name)


def create_user(
    cognito, user_pool_id: str, email: str, temp_password: str, group: str
) -> Tuple[str, str]:
    """Create a Cognito user with a temporary password and attach the user to a group."""
    try:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=temp_password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",
        )
    except cognito.exceptions.UsernameExistsException:
        pass
    cognito.admin_add_user_to_group(
        UserPoolId=user_pool_id, Username=email, GroupName=group
    )
    user = cognito.admin_get_user(UserPoolId=user_pool_id, Username=email)
    sub_attr = next(a["Value"] for a in user["UserAttributes"] if a["Name"] == "sub")
    return email, sub_attr


def main() -> int:
    """Seed an admin and multiple patients into Cognito."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--user-pool-id", required=True)
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--patients", type=int, default=10)
    parser.add_argument("--password", default="TempPassw0rd!")
    args = parser.parse_args()

    cognito = boto3.client("cognito-idp", region_name=args.region)

    ensure_group(cognito, args.user_pool_id, "admin")
    ensure_group(cognito, args.user_pool_id, "patients")

    admin_email, admin_sub = create_user(
        cognito, args.user_pool_id, args.admin_email, args.password, "admin"
    )

    created: List[Tuple[str, str]] = []
    for i in range(1, args.patients + 1):
        email = f"patient{i:03d}@example.com"
        created.append(
            create_user(
                cognito, args.user_pool_id, email, args.password, "patients"
            )
        )

    print("ADMIN:", admin_email, admin_sub)
    for e, s in created:
        print("PATIENT:", e, s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
