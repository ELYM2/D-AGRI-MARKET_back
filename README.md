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

The server is configured with CORS to allow `http://localhost:3000` (Next.js dev).
