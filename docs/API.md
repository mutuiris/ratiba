# API Documentation

Base URL: `https://ratiba-447993598243.africa-south1.run.app`

All API endpoints are prefixed with `/api/`.

## Authentication

The API uses JWT (JSON Web Tokens). Obtain a token pair:

```
POST /api/token
Content-Type: application/json

{"username": "Addy", "password": "addy12345"}
```

Response:

```json
{"access": "eyJ...", "refresh": "eyJ..."}
```

Use the access token in subsequent requests:

```
Authorization: Bearer eyJ...
```

Refresh when expired:

```
POST /api/token/refresh
{"refresh": "eyJ..."}
```

---

## Endpoints

### POST /api/appointments

Book a 30-minute slot for a patient.

**Request:**

```json
{
  "doctor": 1,
  "patient": 1,
  "start_at": "2026-07-15T09:00:00+03:00"
}
```

**Headers:**

```
Idempotency-Key: unique-client-generated-uuid
```

**Success (201):**

```json
{
  "id": 1,
  "doctor": 1,
  "patient": 1,
  "start_at": "2026-07-15T06:00:00Z",
  "end_at": "2026-07-15T06:30:00Z",
  "status": "booked",
  "cancel_reason": "",
  "created_at": "2026-07-14T10:00:00Z",
  "cancelled_at": null
}
```

**Errors:**

| Status | Reason                                                                     |
| ------ | -------------------------------------------------------------------------- |
| 400    | Slot in the past, too soon (< 1hr), outside working hours, off 30-min grid |
| 404    | Unknown patient                                                            |
| 409    | Slot already taken                                                         |

---

### GET /api/doctors//availability?date=YYYY-MM-DD

Return all available 30-minute slots for a doctor on a given date.

**Example:** `GET /api/doctors/1/availability?date=2026-07-15`

**Success (200):**

```json
{
  "date": "2026-07-15",
  "slots": [
    "2026-07-15T06:00:00Z",
    "2026-07-15T06:30:00Z",
    "2026-07-15T07:00:00Z"
  ]
}
```

Slots are in UTC. An empty `slots` array means the doctor has no availability that day.

**Errors:**

| Status | Reason                            |
| ------ | --------------------------------- |
| 400    | Missing or invalid date parameter |
| 404    | Doctor not found                  |

---

### PATCH /api/appointments//cancel

Cancel a booked appointment. The slot becomes available again.

**Request:**

```json
{
  "reason": "Schedule conflict"
}
```

**Success (200):**

```json
{
  "id": 1,
  "doctor": 1,
  "patient": 1,
  "start_at": "2026-07-15T06:00:00Z",
  "end_at": "2026-07-15T06:30:00Z",
  "status": "cancelled",
  "cancel_reason": "Schedule conflict",
  "created_at": "2026-07-14T10:00:00Z",
  "cancelled_at": "2026-07-14T12:00:00Z"
}
```

**Errors:**

| Status | Reason                |
| ------ | --------------------- |
| 403    | Not your appointment  |
| 404    | Appointment not found |
| 409    | Already cancelled     |

---

### PATCH /api/appointments//reschedule

Move an appointment to a new slot. The original slot becomes available, the new slot is validated.

**Request:**

```json
{
  "start_at": "2026-07-16T10:00:00+03:00",
  "doctor": 2
}
```

The `doctor` field is optional - omit it to keep the same doctor.

**Success (200):**

```json
{
  "id": 1,
  "doctor": 2,
  "patient": 1,
  "start_at": "2026-07-16T07:00:00Z",
  "end_at": "2026-07-16T07:30:00Z",
  "status": "booked",
  "cancel_reason": "",
  "created_at": "2026-07-14T10:00:00Z",
  "cancelled_at": null
}
```

**Errors:**

| Status | Reason                                                  |
| ------ | ------------------------------------------------------- |
| 400    | New slot in the past, too soon, outside hours, off-grid |
| 403    | Not your appointment                                    |
| 404    | Appointment not found                                   |
| 409    | Already cancelled, or new slot taken                    |

---

### GET /api/patients//appointments

List a patient's upcoming booked appointments, sorted by date ascending.

**Example:** `GET /api/patients/1/appointments`

**Success (200):**

```json
[
  {
    "id": 1,
    "doctor": 1,
    "patient": 1,
    "start_at": "2026-07-15T06:00:00Z",
    "end_at": "2026-07-15T06:30:00Z",
    "status": "booked",
    "cancel_reason": "",
    "created_at": "2026-07-14T10:00:00Z",
    "cancelled_at": null
  }
]
```

**Errors:**

| Status | Reason                                 |
| ------ | -------------------------------------- |
| 403    | Not your patient record (unless staff) |

---

## Permission Model

- **Patients** can only act on their own appointments and view their own data.
- **Staff** can act on any appointment and view any patient's data.
- The API checks ownership via the JWT-authenticated user's linked Patient record.
