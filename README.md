# AIVOA Complaints Module

AI-assisted Customer Complaint Management module for a pharmaceutical QMS (API and FDF manufacturing).

## Stack

- Backend: FastAPI, PostgreSQL + pgvector, LangGraph, Groq
- Frontend: React, Redux Toolkit, Tailwind CSS

## Backend setup

Requires Python 3.12 and a PostgreSQL 16 database with the `pgvector` extension
available (e.g. the `pgvector/pgvector:pg16` image).

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # then edit it - JWT_SECRET has no default and is required
alembic upgrade head
uvicorn app.main:app --reload
```

Configuration is read from `backend/.env`; see `backend/.env.example` for the
full list of variables and their defaults. Interactive API docs are at
`/docs`, and `/health` is a liveness probe.

## Tests

```bash
cd backend
pytest tests/ -v
```

The suite creates and drops a throwaway database on the server in
`DATABASE_URL`, so it refuses to run unless that host is local. CI does the
same against a service container (see `.github/workflows/backend-tests.yml`).
