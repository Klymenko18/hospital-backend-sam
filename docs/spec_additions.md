# Assignment Clarifications (Spec Additions)

## Endpoints & Contracts
- `GET /health` → `200 {"status":"ok"}`.
- `GET /patient/me` (JWT) → `200 PatientRecord | 401 | 404`.
- `GET /admin/metrics/overview?min_age&max_age` (Admin) → `200 MetricsOverview | 400 | 403`.
- `GET /admin/metrics/diseases?min_age&max_age` (Admin) → `200 {"diseases":{...}} | 400 | 403`.
- `GET /admin/metrics/medications?min_age&max_age` (Admin) → `200 {"medications":{...}} | 400 | 403`.

**Query params**
- `min_age`, `max_age`: numbers (years), inclusive.
- Return `400` if non-numeric, negative, or `min_age > max_age`.

**Schemas**

`PatientRecord`
```json
{
  "patient_id": "uuid-from-cognito-sub",
  "name": "John Smith",
  "sex": "M",
  "date_of_birth": "1980-05-10",
  "bmi": 24.1,
  "medications": ["atorvastatin 20 mg"],
  "diseases": ["hypertension"]
}
