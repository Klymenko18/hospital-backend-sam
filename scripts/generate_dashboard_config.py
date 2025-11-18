from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import boto3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--stack-name", required=True)
    parser.add_argument("--bucket-name", required=True)
    parser.add_argument("--out", default="dashboard/config.js")
    args = parser.parse_args()

    cf = boto3.client("cloudformation", region_name=args.region)
    resp = cf.describe_stacks(StackName=args.stack_name)
    outputs = {o["OutputKey"]: o["OutputValue"] for o in resp["Stacks"][0]["Outputs"]}

    mapping: Dict[str, str] = {
        "region": args.region,
        "userPoolId": outputs["UserPoolId"],
        "userPoolWebClientId": outputs["UserPoolClientId"],
        "domain": outputs["CognitoDomain"],
        "redirectSignIn": outputs["DashboardURL"],
        "redirectSignOut": outputs["DashboardURL"],
        "apiBaseUrl": outputs["HttpApiUrl"],
    }

    tpl = (
        "window.DASHBOARD_CFG = "
        + json.dumps(mapping, indent=2)
        + ";\n"
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tpl, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
