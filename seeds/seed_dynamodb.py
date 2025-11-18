#!/usr/bin/env python3
"""Seed DynamoDB with patient records derived from Cognito users (excludes admin)."""
import argparse
from typing import Dict, Iterable, List
import boto3


def list_all_users(cognito, user_pool_id: str) -> Iterable[Dict]:
    token = None
    while True:
        params = {"UserPoolId": user_pool_id, "Limit": 60}
        if token:
            params["PaginationToken"] = token
        resp = cognito.list_users(**params)
        for u in resp.get("Users", []):
            yield u
        token = resp.get("PaginationToken")
        if not token:
            break


def get_attr(user: Dict, name: str) -> str:
    for a in user.get("Attributes", []):
        if a.get("Name") == name:
            return a.get("Value", "")
    return ""


def build_patient_item(user: Dict) -> Dict:
    return {
        "patient_id": get_attr(user, "sub"),
        "email": get_attr(user, "email"),
        "status": "active",
    }


def upsert_items(dynamo, table_name: str, items: List[Dict]) -> None:
    table = dynamo.Table(table_name)
    with table.batch_writer(overwrite_by_pkeys=("patient_id",)) as batch:
        for it in items:
            batch.put_item(Item=it)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--user-pool-id", required=True)
    parser.add_argument("--table-name", required=True)
    parser.add_argument("--admin-email", default="admin@example.com")
    args = parser.parse_args()

    session = boto3.session.Session(region_name=args.region)
    cognito = session.client("cognito-idp")
    dynamo = session.resource("dynamodb")

    items: List[Dict] = []
    for user in list_all_users(cognito, args.user_pool_id):
        email = get_attr(user, "email") or ""
        if email.lower() == args.admin_email.lower():
            continue
        items.append(build_patient_item(user))

    if not items:
        print("No patients discovered in Cognito. Nothing to write.")
        return

    upsert_items(dynamo, args.table_name, items)
    print(f"Upserted {len(items)} patients into '{args.table_name}'.")


if __name__ == "__main__":
    main()
