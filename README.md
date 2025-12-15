# Pokus (Django + Go + React)

3v3 покемон-баттлы: лобби, матчмейкинг, пошаговый бой, реплеи, статистика и realtime-уведомления.

## Состав
- Backend: Django + DRF, PostgreSQL, JWT (access + refresh), Redis cache
- Go service: Notification Service (WebSocket + HTTP `/notify`)
- Frontend: React + TypeScript (Vite)

## Запуск (Docker)
1) Создай `.env` на основе `.env.example`:
   - `copy .env.example .env` (Windows) или `cp .env.example .env` (Linux/macOS)
2) Подними сервисы:
   - `docker compose up -d --build`
3) Открой:
   - Frontend: `http://localhost:3000`
   - Django API: `http://localhost:8000`
    - Postgres (для pgAdmin): `localhost:5433` (порт хоста)

Прокси в контейнере frontend (Nginx):
- `/api/*` -> Django (Nginx убирает `/api` префикс)
- `/ws` -> Go notify service

## Запуск frontend отдельно (dev)
1) Подними backend сервисы:
   - `docker compose up -d --build db redis django notify`
2) Запусти frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - Открой `http://localhost:5173`

Vite proxy:
- `/api` -> `http://localhost:8000`
- `/ws` -> `ws://localhost:8081/ws`

## Переменные окружения
Смотри `.env.example`.
- `POSTGRES_*` - настройки БД
- `NOTIFY_URL`, `NOTIFY_TOKEN` - адрес и токен Go notify service
- `REDIS_URL` - Redis для Django cache

## API (кратко)
Все эндпоинты (кроме регистрации/логина) требуют `Authorization: Bearer <access>`.

Auth:
- `POST /auth/register` `{ "username": "...", "password": "..." }`
- `POST /auth/login` `{ "username": "...", "password": "..." }`
- `POST /auth/refresh` `{ "refresh": "..." }`

Catalog / Team:
- `GET /catalog?limit=20&offset=0`
- `GET /catalog/search?q=saur&limit=20&offset=0`
- `POST /catalog/team` `{ "pokemon_ids": [1,2,3] }`
- `GET /catalog/team`

Lobby:
- Fast battle: `POST /lobby` `{ "pokemon_ids": [1,2,3] }`
- Private lobby: `POST /lobby/code` `{ "code":"0007", "pokemon_ids":[1,2,3] }`
- Close private lobby: `POST /lobby/code/close` `{ "code":"0007" }`

Battle:
- `GET /battles`
- `GET /battles/{id}`
- `GET /battles/{id}/replay`
- `POST /battle/{id}/turn` (attack/defend/buff/debuff/switch)
- `POST /battle/pve`

Stats:
- `GET /stats/me`

## Go Notification Service
Сервис слушает `:8081`:
- `GET /ws?user_id=<id>` - WebSocket подписка на события пользователя
- `POST /notify` - приём событий от Django (требует `Authorization: Bearer <NOTIFY_TOKEN>`)

Events: `battle_started`, `battle_ended`, `victory`, `defeat`.

## База данных (PostgreSQL)
Схема управляется миграциями Django (`app/migrations`). Пользователи хранятся в стандартной таблице Django (`auth_user`), прикладные сущности - в приложении `app` (см. `app/models.py`). `JSONField` в Postgres хранится как `jsonb`.

ER (упрощенно):
```
auth_user 1--* UserPokemon (uniq user_id+pokemon_id)
auth_user 1--1 ActivePokemon -> UserPokemon
auth_user 1--1 ActiveTeam
auth_user 1--* LobbyEntry (code NULL или "0000", `uniq_lobby_code` для non-null)
auth_user 1--1 Statistics
Battle (p1,p2 -> auth_user) 1--* BattleEvent
```

Таблицы `app_*`:
- `UserPokemon` - персональный каталог пользователя (снимок PokeAPI: `name`, `stats`, `types`)
- `ActiveTeam` - выбранная команда на матч (список `pokemon_ids`, выбирается в каталоге)
- `ActivePokemon` - активный лидер (FK на `UserPokemon`)
- `LobbyEntry` - заявка в матчмейкинг/приватный лобби (команда `team_ids`, `code` индексирован и уникален только для non-null)
- `Battle` - матч (seed, участники, состав команд, `status`; `result` хранит `state`, `pending_actions`, `type_chart`, `outcome`, `replay`, `replay_sig` (HMAC))
- `BattleEvent` - append-only журнал ходов/событий (`turn` + `payload`)
- `Statistics` - агрегаты по пользователю (`wins`, `losses`, `damage`, `crits`, `win_rate`)

## Тесты
Backend:
- `docker compose exec -T django python manage.py test`

Go (через Docker):
- `cd notification`
- `docker run --rm -v ${PWD}:/src -w /src golang:1.23-alpine go test ./...`

Frontend:
- `npm -C frontend test`

## Pre-commit
Хуки для форматирования и линтинга:
- `pip install -r requirements-dev.txt`
- `pre-commit install`
- проверка: `pre-commit run --all-files`

## CI/CD (GitHub Actions)
Workflow: `.github/workflows/ci.yml`
- test: Django tests + Go tests + Frontend tests
- build: сборка Docker образов
- push: push образов в GHCR (на push в `main`)
- deploy: `docker compose -f deploy/docker-compose.prod.yml up -d` (нужен runner с Docker, обычно self-hosted)
