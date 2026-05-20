# AI Support Log

This file documents where and how AI assistance was used during this project,
as required by the evaluation brief.

---

## What was AI-assisted

### Architecture planning
Used AI to map out the full system before writing any code: models, task flow,
API design, and the relationship between Celery, Redis, and Django. The
architecture diagram was AI-generated and then reviewed manually.

### Boilerplate and structure
AI suggested the management command folder structure
(`management/commands/check_urls.py`) and the Celery app setup in
`myproject/celery.py` and `myproject/__init__.py`.

### Code review
Pasted written code into an AI session to catch bugs before moving on.
Specific issues caught this way:
- `response_time_ms` staying `0.0` on exception paths in `tasks.py`
- `time.time()` replaced with `time.monotonic()` for elapsed duration
- `obj.health_checks.count()` corrected to `obj.results.count()` (wrong related_name)
- Typo `errpr_message` in serializer field list

### Test structure
AI suggested the pattern of refactoring `calculate_monitor_status` to accept
a plain list (instead of a monitor object) so unit tests need zero mocking.

---

## What was written independently

- All model field choices and constraints
- Status calculation logic (`utils.py`)
- Exception handling strategy in `tasks.py`
- Serializer field selection and read_only decisions
- The `check-now` returning `202 Accepted` (understood the semantic reasoning)
- `prefetch_related('results')` to solve the N+1 query problem on list view

---

## How AI output was validated

Every AI-suggested code block was read line by line before being used.
Tests were written to verify the logic independently of how it was produced.
The status calculation tests cover every branch explicitly (UP, DOWN, DEGRADED,
UNKNOWN with 0/1/2/3 checks) so there is no ambiguity about whether the logic
is correct regardless of its origin.
