
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
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Start server:
   ```bash
   python manage.py runserver
   ```

## Admin Panel
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
