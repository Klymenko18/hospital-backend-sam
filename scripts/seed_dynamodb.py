#!/usr/bin/env python3
"""
Seed script for DynamoDB patient records.

This script inserts a set of fake patient records into the target DynamoDB table.
The data is intended to be used by the /patient/me and /admin/metrics handlers.
"""

import os
from typing import List, Dict, Any

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


def build_dynamodb_resource(region: str):
    """
    Build and return a DynamoDB resource for the given AWS region.
    """
    return boto3.resource("dynamodb", region_name=region)


def build_fake_patients() -> List[Dict[str, Any]]:
    """
    Build a static list of fake patient records.

    Adjust the non-key attributes to match the project needs.
    Key attributes will be attached dynamically based on the table schema.
    """
    return [
        {
            "email": "patient1@example.com",
            "age": 32,
            "status": "admitted",
            "diagnosis": "Hypertension",
            "room": "101A",
            "cost": 1200,
        },
        {
            "email": "patient2@example.com",
            "age": 45,
            "status": "discharged",
            "diagnosis": "Pneumonia",
            "room": "202B",
            "cost": 2400,
        },
        {
            "email": "patient3@example.com",
            "age": 27,
            "status": "admitted",
            "diagnosis": "Appendicitis",
            "room": "303C",
            "cost": 1800,
        },
        {
            "email": "patient4@example.com",
            "age": 60,
            "status": "admitted",
            "diagnosis": "Diabetes",
            "room": "404D",
            "cost": 3100,
        },
    ]


def ensure_table_exists(table) -> None:
    """
    Ensure that the DynamoDB table exists and is accessible.
    """
    try:
        table.load()
    except ClientError as exc:
        raise RuntimeError(
            f"Unable to load DynamoDB table '{table.name}': {exc}",
        ) from exc


def ensure_key_attributes(
    item: Dict[str, Any],
    key_schema: List[Dict[str, str]],
) -> None:
    """
    Ensure that the item contains all key attributes defined by the table key schema.

    Heuristics:
        - If the key attribute already exists in the item, it is preserved.
        - If the key attribute is 'email', the existing email value is reused.
        - If the key attribute looks like an ID (patient_id, patientId, id, pk),
          the email value is used as the identifier.
        - For an unknown HASH key, the email is used as a fallback identifier.
        - For an unknown RANGE key, a derived value in the form 'PROFILE#<email>' is used.

    Raises:
        RuntimeError: If the key attribute value cannot be inferred.
    """
    email = item.get("email")

    for key_def in key_schema:
        attr_name = key_def.get("AttributeName")
        key_type = key_def.get("KeyType")

        if not attr_name:
            continue

        if attr_name in item and item[attr_name] is not None:
            continue

        if attr_name == "email" and email:
            item[attr_name] = email
            continue

        if attr_name in {"patient_id", "patientId", "pk", "id"} and email:
            item[attr_name] = email
            continue

        if key_type == "HASH" and email:
            item[attr_name] = email
            continue

        if key_type == "RANGE" and email:
            item[attr_name] = f"PROFILE#{email}"
            continue

        raise RuntimeError(
            f"Unable to infer value for key attribute '{attr_name}' "
            f"based on item: {item}",
        )


def seed_table(table, items: List[Dict[str, Any]]) -> None:
    """
    Insert the provided items into the DynamoDB table using a batch writer.
    """
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


def main() -> None:
    """
    Entry point for the DynamoDB seeding script.

    Environment variables:

        REGION or AWS_REGION:
            AWS region. Optional, default is eu-central-1.

        DYNAMODB_PATIENT_TABLE_NAME or PATIENT_TABLE_NAME:
            Name of the DynamoDB table used for patient records. Required.
    """
    region = get_region()
    table_name = get_required_env(
        "DYNAMODB_PATIENT_TABLE_NAME",
        "PATIENT_TABLE_NAME",
    )

    dynamodb = build_dynamodb_resource(region)
    table = dynamodb.Table(table_name)

    ensure_table_exists(table)

    key_schema = table.key_schema
    items = build_fake_patients()

    for item in items:
        ensure_key_attributes(item, key_schema)

    seed_table(table, items)


if __name__ == "__main__":
    main()
