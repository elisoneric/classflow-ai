# ClassFlow AI

Automates the Course Representative's job of asking lecturers whether a scheduled
class is holding, interpreting the reply, and relaying it to the class — see
[PROJECT.md](PROJECT.md) for the full architecture, decisions, and roadmap.

## Stack

FastAPI + PostgreSQL + SQLAlchemy/Alembic (backend) · Redis + RQ + APScheduler
(background jobs/scheduling) · Anthropic Claude (reply interpretation) ·
React + TypeScript + Tailwind + React Query (frontend) · Docker Compose.

## Prerequisites

- Docker Desktop
- (Only for running things outside Docker) Python 3.12+ and Node 22+

## Quickstart (Docker)

1. Copy the environment template and fill in real values (SMTP, IMAP,
   `ANTHROPIC_API_KEY`, and change `JWT_SECRET_KEY`/`COURSE_REP_EMAIL`/
   `COURSE_REP_PASSWORD` from the placeholders):

   ```bash
   cp .env.example .env
   ```

2. Build and start everything (postgres, redis, backend, worker, scheduler,
   frontend):

   ```bash
   docker compose up -d --build
   ```

3. Run migrations and seed the single Course Rep account (there is no public
   signup route by design — this is the only way an account gets created):

   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m scripts.seed_course_rep
   ```

4. Open the app:
   - Frontend: http://localhost:5173
   - Backend API docs: http://localhost:8000/docs

Log in with the `COURSE_REP_EMAIL` / `COURSE_REP_PASSWORD` from your `.env`.

### Everyday use

```bash
docker compose up -d       # start everything
docker compose logs -f     # tail all logs
docker compose down        # stop everything (data persists in the postgres volume)
```

Whenever you change the SQLAlchemy models, generate and apply a migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe the change"
docker compose exec backend alembic upgrade head
```

## Running outside Docker (backend)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# with postgres/redis reachable at localhost (e.g. `docker compose up -d postgres redis`):
export DATABASE_URL="postgresql+asyncpg://classflow:changeme@localhost:5432/classflow"
export JWT_SECRET_KEY="dev-secret"

alembic upgrade head
python -m scripts.seed_course_rep
uvicorn app.main:app --reload          # API on :8000
python worker.py                       # separate terminal — RQ worker
python scheduler_main.py               # separate terminal — APScheduler process
```

### Backend tests

```bash
cd backend
./.venv/Scripts/python.exe -m pytest
```

Needs a reachable Postgres (`docker compose up -d postgres redis` is enough —
tests truncate their own tables before each run and never touch the seeded
`users` row).

## Running outside Docker (frontend)

```bash
cd frontend
npm install
npm run dev       # :5173, defaults to VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run build     # type-checks + production build
npm run lint
```

## Configuration notes

- **Timezone** (`TIMEZONE` in `.env`, default `Africa/Lagos`): drives when the
  daily session-generation job runs and how reminder times are interpreted.
  Change this if you're not in that timezone — see ADR-7 in PROJECT.md.
- **AI confidence threshold** (`AI_CONFIDENCE_THRESHOLD`, default `0.75`):
  below this, a lecturer's reply is queued for your review instead of being
  auto-announced. See ADR-3.
- **Inbound email** (`IMAP_*`): a dedicated mailbox the scheduler polls every
  `IMAP_POLL_INTERVAL_SECONDS`. See ADR-2 for why this is polling rather than
  a webhook.
- **WhatsApp**: not implemented in V1 (ADR-1) — `ContactMethod.WHATSAPP` is
  rejected with a 422 if selected. Student announcements and lecturer
  reminders are both email-only for now.

## Repository layout

```
backend/    FastAPI app — see PROJECT.md §13 for the full clean-architecture layout
frontend/   React app — feature-folder structure under src/features
PROJECT.md  Architecture source of truth: vision, ADRs, schema, API, roadmap
```
