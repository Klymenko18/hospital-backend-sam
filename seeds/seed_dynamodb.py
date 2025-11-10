from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from typing import Dict, List

import boto3
from faker import Faker

DIAGNOSES = [
    "Hypertension",
    "Diabetes",
    "Asthma",
    "Migraine",
    "Anxiety",
    "Depression",
    "Allergic rhinitis",
    "GERD",
    "Osteoarthritis",
    "Back pain",
]


def list_patient_subs(cognito, user_pool_id: str) -> List[str]:
    """Return a list of patient subs from the 'patients' group."""
    subs: List[str] = []
    token = None
    while True:
        resp = cognito.list_users_in_group(
            UserPoolId=user_pool_id, GroupName="patients", Limit=60, NextToken=token
        )
        for u in resp.get("Users", []):
            sub = next(a["Value"] for a in u["Attributes"] if a["Name"] == "sub")
            subs.append(sub)
        token = resp.get("NextToken")
        if not token:
            break
    return subs


def make_record(fake: Faker, patient_id: str) -> Dict:
    """Create a synthetic patient record."""
    full_name = fake.name()
    start = date(1960, 1, 1).toordinal()
    end = date(2010, 12, 31).toordinal()
    dob = date.fromordinal(random.randint(start, end)).isoformat()
    last_visit = (date.today() - timedelta(days=random.randint(0, 365))).isoformat()
    dx = random.sample(DIAGNOSES, k=random.randint(1, 3))
    return {
        "patient_id": patient_id,
        "full_name": full_name,
        "dob": dob,
        "last_visit": last_visit,
        "diagnoses": dx,
    }


def main() -> int:
    """Populate DynamoDB with records for all patient users."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--user-pool-id", required=True)
    parser.add_argument("--table-name", required=True)
    args = parser.parse_args()

    cognito = boto3.client("cognito-idp", region_name=args.region)
    dynamo = boto3.resource("dynamodb", region_name=args.region)
    table = dynamo.Table(args.table_name)
    fake = Faker()

    subs = list_patient_subs(cognito, args.user_pool_id)
    for sub in subs:
        table.put_item(Item=make_record(fake, sub))

    print(f"Inserted/overwritten {len(subs)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
