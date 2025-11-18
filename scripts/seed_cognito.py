#!/usr/bin/env python3
"""
Seed script for Cognito users and groups.

The script creates:
- One admin user and assigns the user to the admin group.
- Multiple patient users and assigns them to the patient group.

It is intended to be run after the infrastructure has been deployed.
"""

import os
from typing import List

import boto3
from botocore.exceptions import ClientError


def get_region() -> str:
    """
    Retrieve AWS region from environment variables or use a default value.
    """
    return (
        os.getenv("AWS_REGION")
        or os.getenv("REGION")
        or "eu-central-1"
    )


def get_required_env(*names: str) -> str:
    """
    Retrieve a required environment variable by trying several possible keys.

    Raises:
        RuntimeError: If no environment variable from the list is set.
    """
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    joined = ", ".join(names)
    raise RuntimeError(f"One of environment variables [{joined}] is required but not set.")


def get_env_with_default(name: str, default: str) -> str:
    """
    Retrieve an environment variable or return the provided default value.
    """
    value = os.getenv(name)
    return value if value else default


def build_cognito_client(region: str):
    """
    Build and return a Cognito IDP client for the given AWS region.
    """
    return boto3.client("cognito-idp", region_name=region)


def ensure_user_exists(
    client,
    user_pool_id: str,
    username: str,
    email: str,
) -> None:
    """
    Ensure that a Cognito user with the given username exists.
    """
    try:
        client.admin_get_user(UserPoolId=user_pool_id, Username=username)
        return
    except client.exceptions.UserNotFoundException:
        pass

    client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": "email", "Value": email},
        ],
        MessageAction="SUPPRESS",
    )


def set_permanent_password(
    client,
    user_pool_id: str,
    username: str,
    password: str,
) -> None:
    """
    Set a permanent password for an existing Cognito user.
    """
    client.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=username,
        Password=password,
        Permanent=True,
    )


def ensure_user_in_group(
    client,
    user_pool_id: str,
    username: str,
    group_name: str,
) -> None:
    """
    Ensure that the user is assigned to the specified Cognito group.
    """
    try:
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"ResourceNotFoundException", "UserNotFoundException"}:
            raise
        if error_code == "InvalidParameterException":
            raise
        raise


def seed_admin(
    client,
    user_pool_id: str,
    admin_email: str,
    admin_password: str,
    admin_group_name: str,
) -> None:
    """
    Create an admin user with the given credentials and add the user to the admin group.
    """
    username = admin_email
    ensure_user_exists(client, user_pool_id, username, admin_email)
    set_permanent_password(client, user_pool_id, username, admin_password)
    ensure_user_in_group(client, user_pool_id, username, admin_group_name)


def parse_patient_emails(raw: str) -> List[str]:
    """
    Parse a comma-separated string of patient emails into a clean list.
    """
    parts = [item.strip() for item in raw.split(",")]
    return [item for item in parts if item]


def seed_patients(
    client,
    user_pool_id: str,
    patient_emails: List[str],
    patient_password: str,
    patient_group_name: str,
) -> None:
    """
    Create patient users with the given password and add them to the patient group.
    """
    for email in patient_emails:
        username = email
        ensure_user_exists(client, user_pool_id, username, email)
        set_permanent_password(client, user_pool_id, username, patient_password)
        ensure_user_in_group(client, user_pool_id, username, patient_group_name)


def main() -> None:
    """
    Entry point for the Cognito seeding script.

    Environment variables:

        REGION or AWS_REGION:
            AWS region. Optional, default is eu-central-1.

        USERPOOL_ID or COGNITO_USER_POOL_ID:
            Cognito User Pool ID. Required.

        COGNITO_ADMIN_EMAIL:
            Admin email. Optional, default is admin@example.com.

        COGNITO_ADMIN_PASSWORD:
            Admin password. Optional, default is Admin!Passw0rd1.

        COGNITO_PATIENT_PASSWORD:
            Patient password. Optional, default is Patient!Passw0rd1.

        COGNITO_ADMIN_GROUP_NAME:
            Admin group name. Optional, default is GroupAdmin.

        COGNITO_PATIENT_GROUP_NAME:
            Patient group name. Optional, default is GroupPatients.

        COGNITO_PATIENT_EMAILS:
            Comma-separated list of patient emails.
            Optional, default is patient1@example.com,patient2@example.com.
    """
    region = get_region()
    user_pool_id = get_required_env("USERPOOL_ID", "COGNITO_USER_POOL_ID")

    admin_email = get_env_with_default("COGNITO_ADMIN_EMAIL", "admin@example.com")
    admin_password = get_env_with_default(
        "COGNITO_ADMIN_PASSWORD",
        "Admin!Passw0rd1",
    )
    patient_password = get_env_with_default(
        "COGNITO_PATIENT_PASSWORD",
        "Patient!Passw0rd1",
    )

    admin_group_name = get_env_with_default(
        "COGNITO_ADMIN_GROUP_NAME",
        "GroupAdmin",
    )
    patient_group_name = get_env_with_default(
        "COGNITO_PATIENT_GROUP_NAME",
        "GroupPatients",
    )

    raw_patient_emails = get_env_with_default(
        "COGNITO_PATIENT_EMAILS",
        "patient1@example.com,patient2@example.com",
    )
    patient_emails = parse_patient_emails(raw_patient_emails)

    client = build_cognito_client(region)

    seed_admin(
        client=client,
        user_pool_id=user_pool_id,
        admin_email=admin_email,
        admin_password=admin_password,
        admin_group_name=admin_group_name,
    )

    seed_patients(
        client=client,
        user_pool_id=user_pool_id,
        patient_emails=patient_emails,
        patient_password=patient_password,
        patient_group_name=patient_group_name,
    )


if __name__ == "__main__":
    main()
