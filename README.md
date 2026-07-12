# Ratiba — Clinic Appointment Booking

> *Ratiba* is an appointment scheduling system for a clinic. Patients book, cancel, and reschedule 30-minute appointments with doctors and no two patients can ever hold the same slot.

---

## The problem

A small clinic with 5 doctors. Each doctor has set working hours and works in 30-minute slots.
A patient sees which slots are free for a given doctor on a given day, picks one, and books it.
Once booked, that slot must not be available to anyone else. Patients can also cancel and
reschedule. The clinic is starting small but wants to grow.

Four operations, all built on one shared notion of a "slot":

| Operation              | What it does                                                                           |
| ---------------------- | -------------------------------------------------------------------------------------- |
| **Book**         | Reserve a slot which must be inside working hours, not in the past, not already taken |
| **Availability** | List the free 30-minute slots for a doctor on a given date                             |
| **Cancel**       | Cancel with a reason; the slot becomes bookable again; error if already cancelled      |
| **Reschedule**   | Move to a new slot; the old slot frees, the new slot is validated as a fresh booking   |

The core representation decision is that a slot is a fixed 30 minute point on a grid, and slots
are  are computed. The system stores only two kinds of fact: the **rules**
(each doctor's weekly working hours plus any time-off) and the **bookings** (one appointment row per
booked slot). The **free** is then a calculation: take the grid the working hours rule implies,
subtract the bookings and the time off.

---

## Data model

Five entities. A doctor has many working hours rows (one per weekday), many time-off rows, and many
appointments. A patient has many appointments. A user with role `patient` links to one patient
record; `staff` users have no patient record.

**User** — authentication identity.

| Field         | Type   | Notes                    |
| ------------- | ------ | ------------------------ |
| id            | int    | PK                       |
| email         | string | login                    |
| role          | string | `patient` or `staff` |
| password_hash | string |                          |

**Patient**

| Field   | Type   | Notes      |
| ------- | ------ | ---------- |
| id      | int    | PK         |
| user_id | int    | FK -> User |
| name    | string |            |
| phone   | string |            |

**Doctor**

| Field | Type   | Notes |
| ----- | ------ | ----- |
| id    | int    | PK    |
| name  | string |       |

**WorkingHours** - the weekly recurring schedule.

| Field      | Type | Notes                       |
| ---------- | ---- | --------------------------- |
| id         | int  | PK                          |
| doctor_id  | int  | FK -> Doctor                |
| weekday    | int  | 0 = Monday,  6 = Sunday   |
| start_time | time | **local** time-of-day |
| end_time   | time | **local** time-of-day |

**TimeOff** — one-off exceptions (a blocked day, a lunch break).

| Field     | Type     | Notes         |
| --------- | -------- | ------------- |
| id        | int      | PK            |
| doctor_id | int      | FK -> Doctor  |
| start_at  | datetime | **UTC** |
| end_at    | datetime | **UTC** |
| reason    | string   |               |

**Appointment** — one booked slot.

| Field         | Type     | Notes                       |
| ------------- | -------- | --------------------------- |
| id            | int      | PK                          |
| doctor_id     | int      | FK -> Doctor                |
| patient_id    | int      | FK -> Patient               |
| start_at      | datetime | **UTC**               |
| end_at        | datetime | **UTC**               |
| status        | string   | `booked` or `cancelled` |
| cancel_reason | string   | nullable                    |
| created_at    | datetime |                             |
| cancelled_at  | datetime | nullable                    |

The one constraint which carries the whole correctness story lives on `Appointment`: a partial
unique index on `(doctor_id, start_at)` covering only rows where `status = 'booked'`. This means at
most one active booking per doctor per exact slot-start. Because it ignores cancelled rows, a full
history can accumulate while the guarantee holds. Its role is expanded in
[No double-booking](#no-double-booking--one-database-constraint).

**On the clinic timezone:** it is a single app level constant (e.g `CLINIC_TIMEZONE = "Africa/Nairobi"`),
not a column - one clinic, so per doctor timezones would be premature. Keeping it in config lets a
future multi site clinic promote it to a column without a redesign.

---

## Components & layers

Each rule has one home, so that a given validation lives and no rule is
duplicated. A request flows through four layers:

- **View** — authentication and object level authorisation
- **Serializer** — stateless input validation: field shapes
- **Service layer** — the domain logic: generate availability, and run the atomic
  book / cancel / reschedule operations inside database transactions, translating a constraint
  violation into a `409`.
- **Database (PostgreSQL)** — the database. The partial unique index and the compare-and-set
  updates.

The service layer exists so that: availability computation and the reschedule
race, can be tested without HTTP and reused by both the API and the UI. Views and serializers stay
thin; the correctness critical logic sits in one testable core. The tests that matter most are the
concurrent ones - two bookings racing for a slot, a reschedule into a slot taken in between, a double
cancel - each asserting that exactly one request wins and no slot is lost or double-held.

---

## Key decisions & trade-offs

### Slots are derived, not stored

**Problem.** How should a "free slot" be represented?

**Options.**

- **(A) Materialise** — pre-create a row for every doctor × day × 30 min; booking flips it to taken.
- **(B) Derive** - store working-hours rules and appointment rows; compute free slots on demand.

**Choice: B.**

Under option A, every schedule change becomes a data migration: changing a doctor's hours
means regenerating rows, cancelling a day means deleting rows, and the slot inventory grows without
bound as the clinic plans further ahead. Under option B, those are non events:

- A doctor changes working hours -> availability simply recomputes and existing bookings are untouched.
- A doctor cancels a whole day -> insert one time-off row; there are no slot rows to delete.
- Growth -> no ever-expanding slot table stretching into the future.

### No double-booking

**Problem.** Two patients select the same 3:00 slot at the sametime. One may win.

**The race:** Check whether 3:00 is free, and if so insert, has a gap:
between the check and the insert, the other request also inserts. Both saw "free", both book. No
amount of application level checking closes this window, because the two requests can interleave in
any order.

**Options considered.** Enforce uniqueness with a database constraint; raise the transaction
isolation level to serializable; take an explicit row lock (`SELECT … FOR UPDATE`); or pre-create
lock rows for every possible slot.

**Choice: the partial unique index.**

The fixed 30-minute grid reduces "no overlapping bookings" to a single rule: no two active bookings
share the same `(doctor_id, start_at)`. The second insert fails on the constraint, which the service
layer turns into a **409** - under ordinary `READ COMMITTED`, with no explicit lock and no deadlock
risk.

### Retry-safe booking

**Problem.** A patient double-taps the booking, or a request times out and the client retries, so the
same booking intent can reach the create endpoint twice.

Booking accepts an `Idempotency-Key` header: a repeated key
returns the original appointment instead of creating a second one, so retries are safe.

### Time - instants are UTC, rules are local

- `Appointment.start_at` and `TimeOff.start_at` are UTC — they are moments in time.
- `WorkingHours.start_time` is a local time of day
- Availability is the only place the two meet: the 30-minute grid is laid out in local time, each
  point is converted to UTC, and the result is compared against UTC bookings.

### Reschedule is one atomic UPDATE

**Problem.** Moving a 3:00 appointment to 4:00 means freeing 3:00 and booking 4:00. If a patient books
4:00 in between, the previous patient lose both slots.

Freeing 3:00 is implicit once the row says 4:00. The same partial index guards the new time: if 4:00 is taken, the UPDATE fails on the constraint, the whole statement rolls back, and the row is left as it was, so the patient keeps 3:00.

### Cancel is a compare-and-set

**Problem.** Cancelling frees the slot and return an error if the appointment is already
cancelled  even when two cancel requests race.

**How the slot frees.** The status flips from `booked` to `cancelled`. The row drops out of the
partial index (`WHERE status = 'booked'`), so the slot is immediately bookable again, and the row
remains for audit (`cancel_reason`, `cancelled_at`). Nothing is deleted.

**The race, and the fix.** Cancellation is a single conditional update: set the status to
`cancelled` only where the row is still `booked`. The rows affected decide the outcome - `1` means
this request cancelled it (`200`), `0` means it was no longer `booked` on arrival (`409 already cancelled`). Because an update takes a row-level write lock, two concurrent cancels serialize: the
first flips the row, the second matches nothing and gets the `409`. One request wins, with no
explicit lock.

### Availability

Availability for a doctor on a date is computed in two queries followed by set arithmetic, with no
per-slot database hits:

1. Look up the doctor's working hours for that weekday. If none, the doctor is off that day and the
   result is empty.
2. Build the 30-minute grid in local time  and convert each point to UTC -
   this is the candidate set.
3. In one query, fetch the booked slot-starts for that doctor within the day; in a second, fetch the
   time-off ranges overlapping the day.
4. The free set is the grid minus booked slots, minus slots overlapping time-off, minus slots that
   fall before "now + 1 hour".
