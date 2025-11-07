# hospital-backend-sam

Minimal-yet-realistic hospital backend built with AWS SAM, Cognito, API Gateway (HTTP API), Lambda (Python), DynamoDB, and an S3-hosted admin dashboard.

## What you get

- Cognito User Pool (+ groups `Patients`, `Admin`)
- HTTP API with JWT Authorizer
- Lambdas:
  - `GET /health`
  - `GET /patient/me` (JWT)
  - `GET /admin/metrics/overview` (Admin, optional `min_age`, `max_age`)
  - `GET /admin/metrics/diseases` (Admin, optional `min_age`, `max_age`)
  - `GET /admin/metrics/medications` (Admin, optional `min_age`, `max_age`)
- DynamoDB table `PatientRecords`
- S3 static dashboard rendering metrics and basic filters
- Seed scripts for Cognito users and DynamoDB records
- OpenAPI + Postman collection
- Basic tests (pytest)

## Prerequisites

- AWS CLI configured
- AWS SAM CLI
- Python 3.11 or newer

## Quick start

```bash
sam build
sam deploy --guided
