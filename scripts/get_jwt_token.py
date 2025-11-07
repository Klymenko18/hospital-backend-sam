from __future__ import annotations

import argparse
import os
import sys
import boto3


def main() -> None:
    """
    Retrieves Cognito ID/Access tokens using USER_PASSWORD_AUTH.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    region = os.getenv("AWS_REGION") or "eu-central-1"
    client_id = os.getenv("USER_POOL_CLIENT_ID")
    if not client_id:
        print("USER_POOL_CLIENT_ID is required", file=sys.stderr)
        sys.exit(1)

    idp = boto3.client("cognito-idp", region_name=region)
    resp = idp.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": args.email, "PASSWORD": args.password},
    )
    auth = resp["AuthenticationResult"]
    print("ID_TOKEN=" + auth["IdToken"])
    print("ACCESS_TOKEN=" + auth["AccessToken"])
    print("REFRESH_TOKEN=" + auth.get("RefreshToken", ""))
    print("EXPIRES_IN=" + str(auth["ExpiresIn"]))


if __name__ == "__main__":
    main()
