#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Iterable

import boto3
from botocore.exceptions import ClientError


def _env(name: str) -> str:
    """Return a required environment variable or fail fast."""
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing environment variable: {name}")
    return val


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def put_if_absent(dynamo, table: str, pk_name: str, item: Dict[str, Any], retries: int = 5) -> None:
    """Put an item if it does not exist, with optimistic condition and bounded retries."""
    attempt = 0
    while True:
        try:
            dynamo.put_item(
                TableName=table,
                Item=item,
                ConditionExpression="attribute_not_exists(#pk)",
                ExpressionAttributeNames={"#pk": pk_name},
            )
            return
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return
            if e.response["Error"]["Code"] in {"ProvisionedThroughputExceededException", "ThrottlingException"} and attempt < retries:
                delay = 2 ** attempt * 0.2
                time.sleep(delay)
                attempt += 1
                continue
            raise


def upsert(dynamo, table: str, pk_name: str, pk_value: str, attrs: Dict[str, Any]) -> None:
    """Upsert non-key attributes for the given primary key."""
    expr_names = {}
    expr_vals = {}
    sets = []
    for i, (k, v) in enumerate(attrs.items(), start=1):
        nk = f"#n{i}"
        vk = f":v{i}"
        expr_names[nk] = k
        expr_vals[vk] = {"S": v} if isinstance(v, str) else v
        sets.append(f"{nk} = {vk}")
    update_expr = "SET " + ", ".join(sets)
    boto3.client("dynamodb").update_item(
        TableName=table,
        Key={pk_name: {"S": pk_value}},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_vals,
    )


def as_item(pk_name: str, patient_email: str, diagnosis: str, updated_iso: str) -> Dict[str, Any]:
    """Build a DynamoDB attribute map for a patient record (string-only schema)."""
    return {
        pk_name: {"S": patient_email},
        "diagnosis": {"S": diagnosis},
        "updatedAt": {"S": updated_iso},
    }


def seed_bulk(dynamo, table: str, items: Iterable[Dict[str, Any]]) -> None:
    """Batch-write a bounded list of items using BatchWriteItem with automatic unprocessed retries."""
    request_items = {table: [{"PutRequest": {"Item": it}} for it in items]}
    while request_items[table]:
        resp = dynamo.batch_write_item(RequestItems=request_items)
        unp = resp.get("UnprocessedItems", {}).get(table, [])
        request_items[table] = unp
        if unp:
            time.sleep(0.5)


def main() -> int:
    """Seed or update the PatientRecords table in an idempotent manner."""
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-central-1"
    table = _env("TABLE")
    pk_name = os.getenv("PK") or "patientId"
    client = boto3.client("dynamodb", region_name=region)

    payload = [
        as_item(pk_name, "patient1@example.com", "Hypertension", "2025-11-11T10:00:00Z"),
        as_item(pk_name, "patient2@example.com", "Type 2 Diabetes", "2025-11-11T10:05:00Z"),
        as_item(pk_name, "patient3@example.com", "Asthma", "2025-11-11T10:10:00Z"),
        as_item(pk_name, "patient4@example.com", "Migraine", "2025-11-11T10:20:00Z"),
    ]
    seed_bulk(client, table, payload)

    put_if_absent(
        client,
        table,
        pk_name,
        as_item(pk_name, "patient5@example.com", "Coronary artery disease", _now_iso()),
    )

    upsert(
        client,
        table,
        pk_name,
        "patient2@example.com",
        {"diagnosis": "Asthma (controlled)", "updatedAt": _now_iso()},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
