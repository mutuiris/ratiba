# AI Reflection

## 1. What did I use AI for?

- **UI**: Helped generate HTML/CSS for the split-screen auth pages and card-based patient views.
- **Implementation**: Assisted with scaffolding the test suite, fixing a timezone display bug where slots showed UTC instead of local time after deployment, debugging database connection issues during Cloud SQL setup, resolving queryset filter logic in the availability computation, and helping me get the `IntegrityError` handling right in the booking and reschedule flows.
- **CI/CD**: Assisted with the GCP setup - specifically Workload Identity Federation configuration, Cloud SQL permissions, and debugging the `DATABASE_URL` format for Cloud Run's socket-based connection.
- **Documentation**: Helped structure these docs and refine how I explained my design decisions.

## 2. One example where AI improved my work

**Prompt**: "In the availability view: views.py, the time slots display 3 hours behind local time but the appointments page shows the correct time. Both use the same data from get_availability. Why the difference?"

**Result**: AI identified that `get_availability()` returns UTC datetimes, and the view was formatting them with `.strftime("%H:%M")` directly -displaying UTC (09:30) instead of Africa/Nairobi local time (12:30). It also caught that `date.today()` uses the server's clock (UTC on Cloud Run), which shows the wrong date around midnight EAT.

The fix AI suggested and I accepted:

```python
# Before (broken — shows UTC time)
fmt = [
    {"iso": s.isoformat(), "display": s.strftime("%H:%M"), "hour": s.hour}
    for s in raw_slots
]

# After (correct — converts to clinic timezone for display)
tz = ZoneInfo(settings.CLINIC_TIMEZONE)
fmt = [
    {
        "iso": s.isoformat(),
        "display": s.astimezone(tz).strftime("%H:%M"),
        "hour": s.astimezone(tz).hour,
    }
    for s in raw_slots
]
```

And for the fallback date:

```python
# Before (server clock, wrong around midnight EAT)
"today": date.today().isoformat()

# After (clinic's local date)
"today": datetime.now(tz).date().isoformat()
```

The `iso` field still submits UTC to the backend for booking - so the display fix doesn't affect the concurrency model. AI correctly identified this as a display concern.

## 3. Example where AI was wrong

Writing the `cancel()` function in `clinic/services/booking.py`, AI suggested a `.get()` then `.save()` pattern - fetch the appointment, check if it's booked, then update and save. I noticed that this has a race condition: two concurrent cancel requests could both read `status="booked"` and both succeed, with one overwriting the other's `cancel_reason`. Pushed back and switched to the `.filter(status="booked").update(...)` pattern that does the check and write in a single SQL statement.

## 4. Two decisions I made without AI

1. **Partial unique index over application level locking**: I chose a database constraint to prevent double-booking instead of `SELECT FOR UPDATE` or serializable isolation.
2. **Update-in-place for reschedule**: Cancel-then-book has a race window where the patient loses their original slot. I went with a single `UPDATE` inside `transaction.atomic()` so the row never becomes "free" mid-operation.
