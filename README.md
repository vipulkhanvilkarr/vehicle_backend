
# Vehicle Backend API Documentation

## Overview
This Django REST API manages vehicles and users with role-based permissions. It supports CRUD operations for vehicles and user management, with special access for SUPER_ADMIN users. Authentication is handled by a custom 128-byte token system.

## Features
- Custom token-based authentication (32-byte tokens, stored in DB)
- Role-based access control (SUPER_ADMIN, ADMIN, USER)
- Vehicle CRUD (Create, Read, Update, Delete)
- User CRUD (Create, Update, Delete by SUPER_ADMIN)
- Flexible vehicle type handling for frontend integration

## API Endpoints

### Authentication
- `POST /auth/login/` — Obtain custom auth token (returns 32-byte token)
- `POST /auth/logout/` — Invalidate current token (requires Authorization header)

### User Management
- `GET /current-user-details/` — Get current user info
- `POST /users/create/` — Create user (SUPER_ADMIN only)
- `PUT/PATCH /users/update/<id>` — Update user (SUPER_ADMIN only)
- `DELETE /users/delete/<id>` — Delete user (SUPER_ADMIN only)

### Vehicle Management
- `GET /vehicles/` — List all vehicles
- `POST /vehicles/create/` — Create vehicle
- `PUT/PATCH /vehicles/<id>/update/` — Update vehicle
- `DELETE /vehicles/<id>/delete/` — Delete vehicle (SUPER_ADMIN only)

### Vehicle Types
- `GET /vehicle-types/` — List all available vehicle types (for frontend dropdowns)

## Vehicle Type Handling
- Frontend should use dropdown options: `"Two Wheeler"`, `"Three Wheeler"`, `"Four Wheeler"`
- Backend only accepts these exact values (case-sensitive)
- API always returns human-readable value for vehicle_type

## Models
### User
- `username`: string
- `password`: string
- `role`: SUPER_ADMIN | ADMIN | USER

### Vehicle
- `vehicle_number`: string (unique, alphanumeric)
- `vehicle_type`: string ("Two Wheeler", "Three Wheeler", "Four Wheeler")
- `vehicle_model`: string
- `vehicle_description`: string

### AuthToken (Custom Token Model)
- `key`: string (32-byte hex, unique)
- `user`: FK to User
- `created`: datetime
- `is_active`: boolean (only one active token per user at a time)

### VehicleType
- `name`: string (unique, one of allowed types)

## Permissions
- Only SUPER_ADMIN can create, update, or delete users
- Only SUPER_ADMIN can delete vehicles
- ADMIN and USER can view vehicles

## Authentication
- All endpoints (except login) require authentication
- Use the token from `/auth/login/` in the `Authorization` header:
  - `Authorization: Token <token>` **or** `Authorization: Bearer <token>`
- Logout by sending a POST to `/auth/logout/` with the same header; this deactivates the token in the database

## Setup & Run
1. Edit **`.env`** in the **repo root** (same folder as `docker-compose.yml`): set `POSTGRES_*`, `SECRET_KEY`, and for production `DEBUG=False` and `ALLOWED_HOSTS` to your domain(s).

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. From the `backend` folder, run migrations and the server:
   ```bash
   cd backend
   python manage.py migrate
   python manage.py runserver
   ```

**Docker:** `docker compose up -d --build` starts Redis + app + Celery. Postgres connection comes from your **`.env`** (`POSTGRES_HOST`, `POSTGRES_PORT`, etc.). Containers use `host.docker.internal` to reach Postgres on the host (see **Deploy on a Linux server** below). To use the **bundled** Postgres container instead, run with profile: `docker compose --profile bundled-db up -d --build` and set `POSTGRES_HOST=db` in `.env`.

## Deploy on a Linux server (Docker + Postgres already on the host)

1. **On the server**, install Git if needed, then clone or copy this project into a folder (for example `/opt/vehicle_backend`).

2. **PostgreSQL on the host** — create the same database and user as in your `.env` (example names from the template):
   ```bash
   sudo -u postgres psql -c "CREATE USER vehicle_user WITH PASSWORD 'your_secure_password';"
   sudo -u postgres psql -c "CREATE DATABASE vehicle_db OWNER vehicle_user;"
   ```
   Adjust names to match `POSTGRES_USER` / `POSTGRES_DB` in `.env`.

3. **Allow Docker to connect to Postgres** — in `postgresql.conf` set `listen_addresses = '*'` (or at least include the Docker bridge). In `pg_hba.conf` add a line for Docker clients, for example:
   ```
   host all all 172.16.0.0/12 scram-sha-256
   ```
   Then reload Postgres: `sudo systemctl reload postgresql` (or your distro’s equivalent).

4. **Server `.env`** (repo root) — production-style values, and **point at the host**:
   ```env
   DEBUG=False
   SECRET_KEY=<strong-random-secret>
   ALLOWED_HOSTS=your.domain.com,your.server.ip
   POSTGRES_DB=vehicle_db
   POSTGRES_USER=vehicle_user
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_HOST=host.docker.internal
   POSTGRES_PORT=5432
   CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
   CORS_ALLOW_ALL_ORIGINS=False
   ```
   Leave `DATABASE_URL` unset unless you use a managed URL with SSL.

5. **Build and run:**
   ```bash
   cd /opt/vehicle_backend
   docker compose up -d --build
   ```
   API listens on port **8000**. Put Nginx or Caddy in front for HTTPS on 443 if you need it.

6. **Firewall:** open **8000** (or only **80/443** if a reverse proxy forwards to 8000).

If `host.docker.internal` fails on an old Docker build, set `POSTGRES_HOST` to your server’s LAN IP or to `172.17.0.1` (default Docker bridge gateway on many Linux installs), and keep Postgres listening on that interface.
- Access at `/admin/`
- Manage users, vehicles, and tokens via GUI

## Notes
- All endpoints require authentication except `/auth/login/`
- Use the custom token system for all API requests
- Vehicle type is always returned as a user-friendly string

## Security

### XSS Protection

- The backend is a pure JSON API (Django REST Framework), so no dynamic HTML rendering from user input.
- All user-facing text fields (`vehicle_model`, `vehicle_description`) are sanitized using `django.utils.html.strip_tags` to strip any HTML tags (e.g. `<script>`).
- On the frontend (React), all output is automatically escaped and we avoid using `dangerouslySetInnerHTML`.


### IPFilter Middleware Fix

**Problem**

backend was returning:

   Access denied: IP not allowed

because the middleware only allowed:

   ALLOWED_IPS = ["127.0.0.1", "::1"]

So Render, Vercel, Postman, and real users were blocked.

**Solution**

updated the middleware so that:

- When running in production (`DEBUG=False`), IP filtering is disabled
- When running locally (`DEBUG=True`), only localhost is allowed

This means:

🟢 **Production (Render)** → Everyone can access normally
🟡 **Local Dev** → Still protected from outside access

And your `.env` now correctly has:

   DEBUG=False
   ALLOWED_IPS=

---
For further details, see code comments and docstrings in the source files.
