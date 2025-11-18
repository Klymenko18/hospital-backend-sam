Hospital Mini Backend – Short Overview
What this project is for

This is a minimal backend that shows how to build a Cognito-protected, serverless API on AWS for a hospital (or any domain where you have “normal users + admins” and some entity stored in DynamoDB).

Typical real-world use cases:

Patient portal: patient logs in and sees their own profile / status (/patient/me).

Admin dashboard: admin sees aggregated stats over all patients (/admin/metrics).

Generic pattern: “per-user resource + admin metrics” behind Cognito groups, ready to be extended with more endpoints (appointments, doctors, billing, etc.).

Tech stack: AWS SAM, API Gateway HTTP API, Lambda (Python), Cognito User Pool, DynamoDB.

How to test locally against AWS

Assuming AWS CLI, SAM, Python 3.9, and jq are installed and credentials are configured.

1. Build and deploy
sam build
sam deploy --guided   # first time
# then later:
sam deploy


After deploy, fetch outputs:

export REGION=eu-central-1
export STACK=hospital-mini-stack

export API_URL=$(aws cloudformation describe-stacks \
  --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text)

export USERPOOL_ID=$(aws cloudformation describe-stacks \
  --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text)

export CLIENT_ID=$(aws cloudformation describe-stacks \
  --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
  --output text)

export TABLE_NAME=$(aws cloudformation describe-stacks \
  --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='PatientTableNameOut'].OutputValue" \
  --output text)

2. Seed Cognito users and groups
export ADMIN_USER=admin@example.com
export PATIENT1=patient1@example.com
export PATIENT2=patient2@example.com

# create admin + patients
# (passwords: Admin!Passw0rd1 / Patient!Passw0rd1)
# ...
# add to groups:
#   admin → GroupAdmin
#   patients → GroupPatients


(You already have the exact commands; they can be kept in a scripts/ shell file if desired.)

3. Seed DynamoDB data
aws dynamodb put-item \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --item '{
    "patientId": {"S": "patient1@example.com"},
    "status":    {"S": "active"},
    "age":       {"N": "30"},
    "name":      {"S": "John Doe"}
  }'

4. Call the endpoints

Healthcheck (no auth):

curl -sS "$API_URL/health" | jq


Patient view (/patient/me):

AUTH_PATIENT=$(aws cognito-idp initiate-auth --region "$REGION" \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$PATIENT1",PASSWORD='Patient!Passw0rd1')

ID_TOKEN_PATIENT=$(echo "$AUTH_PATIENT" | jq -r '.AuthenticationResult.IdToken')

curl -sS "$API_URL/patient/me" \
  -H "Authorization: Bearer ${ID_TOKEN_PATIENT}" | jq


Admin metrics (/admin/metrics):

AUTH_ADMIN=$(aws cognito-idp initiate-auth --region "$REGION" \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME="$ADMIN_USER",PASSWORD='Admin!Passw0rd1')

ID_TOKEN_ADMIN=$(echo "$AUTH_ADMIN" | jq -r '.AuthenticationResult.IdToken')

curl -sS "$API_URL/admin/metrics" \
  -H "Authorization: Bearer ${ID_TOKEN_ADMIN}" | jq

Where things live
hospital-backend-sam/
  src/
    handlers/
      health.py        # GET /health
      patient_me.py    # GET /patient/me (Cognito user + DynamoDB record)
      admin_metrics.py # GET /admin/metrics (admin-only, aggregates)
  template.yaml        # SAM template: API Gateway, Lambdas, Cognito, DynamoDB
  samconfig.toml       # saved SAM deploy configuration
  events/              # sample events for local invoke (optional)
  seeds/               # local tools for generating/seeding data (not deployed)
  scripts/             # place for CLI helper scripts (Cognito/DynamoDB) 
  README.md            # this documentation
