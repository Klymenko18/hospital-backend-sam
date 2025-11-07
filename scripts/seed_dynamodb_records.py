from __future__ import annotations

import argparse
import csv
import os
from typing import Dict, List

import boto3
from faker import Faker


DISEASES = [
    "hypertension",
    "type 2 diabetes",
    "asthma",
    "hyperlipidemia",
    "coronary artery disease",
    "depression",
    "anxiety",
]

MEDS = [
    "lisinopril 10 mg",
    "metformin 500 mg",
    "atorvastatin 20 mg",
    "amlodipine 5 mg",
    "albuterol inhaler",
]


def main() -> None:
    """
    Inserts DynamoDB patient items using sub from CSV.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN", "false") == "true")
    args = parser.parse_args()

    region = os.getenv("AWS_REGION") or "eu-central-1"
    table_name = os.getenv("TABLE_NAME")
    if not table_name:
        raise RuntimeError("TABLE_NAME is required")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    fake = Faker()

    with open(args.csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub = row["sub"]
            profile = {
                "patient_id": sub,
                "name": fake.name(),
                "sex": fake.random_element(elements=["M", "F", "X"]),
                "date_of_birth": fake.date_between(start_date="-85y", end_date="-18y").strftime("%Y-%m-%d"),
                "bmi": round(fake.random_uniform(17.0, 39.0), 1),
                "medications": fake.random_choices(elements=MEDS, length=fake.random_int(0, 3), unique=True),
                "diseases": fake.random_choices(elements=DISEASES, length=fake.random_int(0, 3), unique=True),
            }
            if not args.dry_run:
                table.put_item(Item=profile)
            else:
                pass


if __name__ == "__main__":
    main()
