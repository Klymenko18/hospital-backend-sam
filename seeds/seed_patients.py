"""Seed DynamoDB PatientRecords using Cognito subs as keys."""

from __future__ import annotations

import os
from typing import Dict, List

import boto3


def put_sample_records(sub_by_email: Dict[str, str]) -> None:
    table_name = os.environ["TABLE_NAME"]
    ddb = boto3.resource("dynamodb").Table(table_name)

    samples = [
        {
            "fullName": "Alice Doe",
            "dob": "1990-05-10",
            "conditions": ["hypertension"],
            "allergies": ["penicillin"],
            "lastVisitAt": "2025-10-12",
            "doctorId": "doc-001",
        },
        {
            "fullName": "Bob Smith",
            "dob": "1985-03-21",
            "conditions": ["diabetes", "asthma"],
            "allergies": [],
            "lastVisitAt": "2025-09-02",
            "doctorId": "doc-002",
        },
        {
            "fullName": "Carol Johnson",
            "dob": "2001-01-15",
            "conditions": [],
            "allergies": ["nuts"],
            "lastVisitAt": "2025-08-20",
            "doctorId": "doc-001",
        },
    ]

    emails = [e for e in sub_by_email.keys() if e.startswith("patient")]
    for i, email in enumerate(emails):
        sub = sub_by_email[email]
        data = samples[i % len(samples)].copy()
        data["patientId"] = sub
        ddb.put_item(Item=data)


if __name__ == "__main__":
    # Provide a mapping file created from seed_users.py printed output or rebuild here.
    # Simpler path: re-query Cognito for all patients.
    pool_id = os.environ["USER_POOL_ID"]
    table_name = os.environ["TABLE_NAME"]
    client = boto3.client("cognito-idp")
    subs: Dict[str, str] = {}

    token: str | None = None
    while True:
        resp = client.list_users(UserPoolId=pool_id, PaginationToken=token) if token else client.list_users(UserPoolId=pool_id)
        for u in resp["Users"]:
            email = next((a["Value"] for a in u["Attributes"] if a["Name"] == "email"), None)
            sub = next((a["Value"] for a in u["Attributes"] if a["Name"] == "sub"), None)
            if email and sub and email.startswith("patient"):
                subs[email] = sub
        token = resp.get("PaginationToken")
        if not token:
            break

    put_sample_records(subs)
    print({"seeded": len(subs)})
