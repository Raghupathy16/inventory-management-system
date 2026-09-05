# Inventory & Procurement Management System

> **Status:** Phase 1 of 19 — project scaffolding + database connectivity only.
> A full, polished README (architecture, API docs, screenshots, etc.) will be written in Phase 19.
> See `phase-0-architecture.md` for full requirements and design.

## Running Phase 1 locally (Docker)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# From the project root
docker compose up --build
```

This starts:
- `db` — MySQL 8.0, exposed on `localhost:3306`
- `backend` — FastAPI app, exposed on `localhost:8000`

Wait for the logs to show the backend has started, then visit:

- http://localhost:8000/health — should return a JSON response confirming the API **and** database are both reachable
- http://localhost:8000/docs — FastAPI's auto-generated interactive API docs (Swagger UI)

To stop:
```bash
docker compose down
```

To stop and wipe the database volume (start completely fresh):
```bash
docker compose down -v
```

## Running the backend without Docker (optional, for local development)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Requires a MySQL server running locally; edit backend/.env so DB_HOST=localhost
uvicorn app.main:app --reload
```

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Phase 1 only tests configuration loading — there's no business logic yet.
Business-logic tests (auth, purchase orders, inventory rules, etc.) are
added starting Phase 3.

## Environment variables

See `backend/.env.example` and `.env.example` (root). Copy each to `.env`
in the same directory and fill in real values. **Never commit `.env` files**
— they're git-ignored on purpose.

| Variable | Where | Purpose |
|---|---|---|
| `DB_HOST` | backend/.env | `db` when using Docker Compose, `localhost` otherwise |
| `DB_PORT` | backend/.env | MySQL port, default 3306 |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | backend/.env **and** root .env | Must match in both files |
| `SECRET_KEY` | backend/.env | Used for JWT signing starting Phase 3 |

## Project structure

See `phase-0-architecture.md` for the full backend/frontend folder plan.

## Roadmap

19 phases, from database design through deployment. Full list in
`phase-0-architecture.md`, Section 14.
