## Frontend (React + TypeScript + shadcn/ui)

Minimal dark UI for the Django API + Go notifications service.

### Run (Docker, full stack)
- From repo root: `docker compose up --build`
- Frontend: `http://localhost:3000`
- Django API: `http://localhost:8000`
- Notifications WS: `ws://localhost:8081/ws?user_id=<id>`

The frontend container proxies `/api/*` to Django and `/ws` to the Go service.

To avoid SPA route conflicts on refresh, API calls go through `/api/*` (the proxy strips `/api` before forwarding to Django).

### Run (local dev)
1) Start backend services (db/redis/django/notify) via Docker:
   - `docker compose up --build db redis django notify`
2) Start frontend dev server:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - Open `http://localhost:5173`

### Config
- Optional API override (bypass proxy): `VITE_API_BASE_URL=http://localhost:8000`
- Optional WS override: `VITE_NOTIFY_WS_URL=ws://localhost:8081/ws`
