---
name: run-tests
description: Use when the user wants to execute, debug, or expand the chatbot library's pytest suite. Triggers include "run tests", "pytest", "test failure", or anything that implies validating Python changes in this repo.
---

# Running the chatbot test suite

This library uses `pytest` with `pytest-asyncio` (auto mode) configured in
`pyproject.toml`. Tests live under `tests/` and mirror the package layout
under `src/chatbot/`.

## Quick reference

```bash
# All tests
pytest tests/ -v

# A single module
pytest tests/test_storage.py -v

# A single test
pytest tests/test_tools.py::test_code_interpreter_returns_stdout -v

# Stop on first failure, show local variables
pytest tests/ -x --showlocals

# With coverage (requires `pip install pytest-cov`)
pytest tests/ --cov=chatbot --cov-report=term-missing
```

## Conventions

- `tests/conftest.py` provides shared fixtures — read it before writing new
  tests so you do not duplicate setup.
- Async tests do **not** need `@pytest.mark.asyncio` (auto mode is on).
- Storage tests use in-memory backends by default. Postgres and Redis tests
  are gated behind environment variables (`POSTGRES_URL`, `REDIS_URL`).
- Use `httpx.AsyncClient` for integration tests against FastAPI / Starlette
  adapters — never spin up a real uvicorn process inside a test.

## Adding a test for a bug fix

1. Reproduce the bug as the first assertion of a new test.
2. Confirm the test fails on the unpatched code (`pytest -x` should stop on it).
3. Apply the fix in `src/chatbot/`.
4. Re-run only that test, then the full suite.
