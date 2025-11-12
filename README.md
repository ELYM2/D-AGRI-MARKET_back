## Backend (Django)

Local development:

1) Install deps (using pip):

```
cd appback
pip install -e .
```

Or install from `pyproject.toml` with uv:

```
cd appback
uv sync
```

2) Run migrations and start server:

```
cd appback
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

API endpoints:

- `GET /api/health/` → basic health check

Auth (JWT):

- `POST /api/auth/register/` { username, email?, password } → { user, access, refresh }
- `POST /api/auth/login/` { username, password } → { access, refresh }
- `POST /api/auth/refresh/` { refresh } → { access }
- `POST /api/auth/logout/` { refresh } → blacklist refresh (205)
- `GET /api/auth/me/` (Authorization: Bearer <access>)

The server is configured with CORS to allow `http://localhost:3000` (Next.js dev).

## Use PostgreSQL (optional but recommended)

1) Install dependencies (driver already listed: `psycopg[binary]`). If needed:

```
pip install "psycopg[binary]"
```

2) Create `.env` in `appback/` (or copy the example):

```
cp .env.example .env
```

Edit values to match your local PostgreSQL instance.

3) Run migrations on Postgres and start:

```
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Note: If `POSTGRES_DB` is set, Django will use Postgres instead of SQLite automatically.
