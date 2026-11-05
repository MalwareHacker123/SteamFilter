# Steam 2.0 REST API — Technical Documentation

## Overview
The Steam 2.0 REST API provides programmatic endpoints to interact with Steam catalog data, live player statistics, and authenticated user reviews stored in the `steam_db` PostgreSQL database.

- **Base URL:** `http://127.0.0.1:5000/api`
- **Data Format:** JSON (`application/json`)
- **Authentication:** Session Cookies via `Flask-Login`

---

## Authorization Matrix

| Endpoint | Method | Security Level | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/login` | `POST` | Public | Authenticates credentials and sets session cookie |
| `/api/logout` | `POST` | Logged In | Destroys current user session |
| `/api/me` | `GET` | Logged In | Returns logged-in user profile & role |
| `/api/games` | `GET` | Public | Search catalog with filters (`q`, `genre`, `min_rating`, `max_price`) |
| `/api/games/top-rated` | `GET` | Public | List highest rated games by review count |
| `/api/games/most-played` | `GET` | Public | List games ordered by live player count |
| `/api/games/free` | `GET` | Public | List top-rated free-to-play games |
| `/api/games/<id>` | `GET` | Public | Get game metadata and associated user reviews |
| `/api/reviews` | `POST` | Logged In | Submit a new user review (`viewer` or `admin`) |
| `/api/my-reviews` | `GET` | Logged In | List all reviews submitted by current user |
| `/api/admin/games` | `POST` | Admin Only | Insert or update game records in catalog |
| `/api/admin/reviews/<id>` | `DELETE` | Admin Only | Remove any specified user review |

---

## Key Endpoints & Payloads

### 1. User Authentication (`POST /api/login`)
- **Request Body:**
  ```json
  {
    "username": "sam",
    "password": "sams_password"
  }
