# 🚨 RESQ — Emergency & Safety Management System
### Shared Backend & Admin Command Center Module

> **RESQ** is a unified campus emergency management platform built with **Django 5**, **Django REST Framework (DRF)**, **Django Channels (WebSockets)**, **JWT Authentication**, and **Server-Rendered Bootstrap 5 Admin Dashboard**.

---

## 🏛️ System Architecture Overview

The RESQ ecosystem connects three integrated stakeholders:

```
+-----------------------------------------------------------------------------------+
|                                RESQ ECOSYSTEM                                     |
|                                                                                   |
|  [ Person 1: User / SOS App ]  --->  POST /api/incidents/                         |
|  (Students report emergencies)            |                                       |
|                                           v                                       |
|                            [ SHARED DJANGO BACKEND ]                              |
|                            * PostgreSQL / SQLite                                  |
|                            * JWT Auth & Role System                               |
|                            * Channels WebSocket Layer                             |
|                             /                    \                                |
|                            /                      \                               |
|                           v                        v                              |
|   [ Person 2: Responder App ]           [ Person 3: Admin Command Dashboard ]     |
|   (Accept, En-Route, Resolve)           (Live WebSockets, Dispatch, Analytics)   |
+-----------------------------------------------------------------------------------+
```

- **Person 1 (User App)**: Mobile/Web app where students and campus staff raise SOS distress signals, report hazard incidents with GPS coordinates, and view incident status.
- **Person 2 (Response Team App)**: Responder mobile/web app for campus security, medical units, and fire squads to toggle on-duty availability, accept dispatched emergencies, and transition incident lifecycle statuses.
- **Person 3 (Admin Command Center)**: Real-time mission control with live WebSocket event stream, manual dispatch override, team management, user directory, and interactive Chart.js analytics.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Redis server (Optional for production scale; defaults to in-memory channel layer for instant local zero-config dev)

### 2. Installation

```bash
# 1. Clone or navigate to the repository directory
cd RESQ

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` (or let the default fallback run out of the box):

```bash
cp .env.example .env
```

Key environment variables:
- `DEBUG=True`
- `SECRET_KEY=your-secret-key`
- `DATABASE_URL=postgres://user:pass@localhost:5432/resq_db` *(Leave empty to use local `db.sqlite3`)*
- `USE_REDIS=false` *(Set to `true` and configure `REDIS_URL` if running Redis)*
- `REDIS_URL=redis://127.0.0.1:6379/0`

### 4. Database Migrations & Demo Seed Data

```bash
# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Seed database with demo admin, 5 response teams, 15 students, and 22 realistic incidents
python manage.py seed_demo_data
```

### 5. Running the Server (ASGI with WebSockets)

```bash
# Run using Daphne ASGI server (handles both HTTP and WebSockets)
python manage.py runserver
```

Open your browser to **`http://localhost:8000/`** or **`http://localhost:8000/admin-dashboard/`**.

---

## 🔐 Default Demo Accounts

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full dashboard access & superuser |
| **Responder (EMS)** | `responder_medic` | `password123` | Campus EMS Unit 1 (Hostel Block) |
| **Responder (Alpha)** | `responder_alpha` | `password123` | Alpha Tactical Patrol (North Complex) |
| **Responder (Fire)** | `responder_fire` | `password123` | Fire & Hazmat Squad (Science Complex) |
| **Responder (Night)** | `responder_night` | `password123` | Night Safety Escort (Library Hub) |
| **Responder (Delta)** | `responder_delta` | `password123` | Delta Multi-Hazard (Sports Arena) |
| **Student Users** | `alex_rivera`, `priya_sharma`, `jordan_lee`, ... | `password123` | 15 student accounts available |

---

## 📡 REST API CONTRACT (For Person 1 & Person 2)

All protected API endpoints require an Authorization Header with the JWT Bearer token:
```http
Authorization: Bearer <access_token>
```

---

### 1. Authentication Endpoints

#### `POST /api/auth/register/`
Registers a new user (Student or Responder).

- **Request Body:**
```json
{
  "username": "sarah_connor",
  "email": "sarah@campus.edu",
  "password": "securepassword123",
  "confirm_password": "securepassword123",
  "first_name": "Sarah",
  "last_name": "Connor",
  "phone": "+1-555-0199",
  "role": "user"
}
```

- **Response (`201 Created`):**
```json
{
  "message": "User registered successfully.",
  "user": {
    "id": 16,
    "username": "sarah_connor",
    "email": "sarah@campus.edu",
    "first_name": "Sarah",
    "last_name": "Connor",
    "role": "user",
    "phone": "+1-555-0199",
    "status": "active"
  },
  "tokens": {
    "refresh": "eyJhbGciOi...",
    "access": "eyJhbGciOi..."
  }
}
```

---

#### `POST /api/auth/login/`
Authenticates a user and returns JWT access + refresh tokens.

- **Request Body:**
```json
{
  "username": "responder_medic",
  "password": "password123"
}
```

- **Response (`200 OK`):**
```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi...",
  "user": {
    "id": 3,
    "username": "responder_medic",
    "email": "responder_medic@resq.edu",
    "first_name": "Dr. Sarah",
    "last_name": "Jenkins",
    "role": "responder",
    "phone": "+1-555-0202",
    "status": "active"
  },
  "team": {
    "id": 2,
    "name": "Campus EMS Unit 1",
    "zone": "Hostel & Residential Block",
    "incident_types": ["medical"],
    "availability_status": "on-duty",
    "cases_handled": 18,
    "avg_response_time": 3.2
  }
}
```

---

#### `POST /api/auth/refresh/`
Refreshes an expired JWT access token.

- **Request Body:**
```json
{
  "refresh": "eyJhbGciOi..."
}
```

- **Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOi..."
}
```

---

### 2. Incidents Endpoints (Person 1 & Person 2)

#### `POST /api/incidents/` — Create / Report Incident (Person 1)
Report an emergency or SOS distress signal. Automatically notifies Admin dashboard via WebSockets.

- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
```json
{
  "incident_type": "medical",
  "description": "Student fell from stairs on 2nd floor, head injury bleeding.",
  "location_lat": 12.9716,
  "location_lng": 77.5946,
  "address": "North Academic Complex, Block 2 Staircase"
}
```
*Valid `incident_type` choices: `"medical"`, `"fire"`, `"security"`, `"harassment"`, `"other"`*

- **Response (`201 Created`):**
```json
{
  "id": 23,
  "incident_type": "medical",
  "description": "Student fell from stairs on 2nd floor, head injury bleeding.",
  "location_lat": 12.9716,
  "location_lng": 77.5946,
  "address": "North Academic Complex, Block 2 Staircase",
  "status": "pending",
  "created_at": "2026-08-31T05:30:00Z"
}
```

---

#### `GET /api/incidents/` — List Incidents
Fetch active and historical incidents. Students see their own reported incidents; responders and admins see all.

- **Headers:** `Authorization: Bearer <token>`
- **Query Parameters (Optional):**
  - `status`: `"pending" | "accepted" | "in-progress" | "resolved" | "rejected"`
  - `type`: `"medical" | "fire" | "security" | "harassment" | "other"`
  - `zone`: e.g. `"North"`, `"Hostel"`
  - `search`: free-text search across address, description, and reporter username

- **Response (`200 OK`):**
```json
{
  "count": 23,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 23,
      "incident_type": "medical",
      "incident_type_display": "Medical Emergency",
      "description": "Student fell from stairs on 2nd floor, head injury bleeding.",
      "location_lat": 12.9716,
      "location_lng": 77.5946,
      "address": "North Academic Complex, Block 2 Staircase",
      "status": "pending",
      "status_display": "Pending / Unassigned",
      "reported_by": 6,
      "reported_by_details": {
        "id": 6,
        "username": "alex_rivera",
        "phone": "+1-555-0301",
        "name": "Alex Rivera"
      },
      "assigned_team": null,
      "assigned_team_details": null,
      "created_at": "2026-08-31T05:30:00Z",
      "resolved_at": null
    }
  ]
}
```

---

#### `GET /api/incidents/<id>/` — Incident Detail + Timeline
Retrieve full incident details including historical status transition logs.

- **Headers:** `Authorization: Bearer <token>`
- **Response (`200 OK`):**
```json
{
  "id": 23,
  "reported_by": {
    "id": 6,
    "username": "alex_rivera",
    "email": "alex_rivera@campus.edu",
    "phone": "+1-555-0301"
  },
  "incident_type": "medical",
  "incident_type_display": "Medical Emergency",
  "description": "Student fell from stairs on 2nd floor, head injury bleeding.",
  "location_lat": 12.9716,
  "location_lng": 77.5946,
  "address": "North Academic Complex, Block 2 Staircase",
  "status": "pending",
  "status_display": "Pending / Unassigned",
  "assigned_team": null,
  "status_log": [
    {
      "id": 45,
      "status": "pending",
      "updated_by": 6,
      "updated_by_name": "alex_rivera",
      "updated_by_role": "user",
      "timestamp": "2026-08-31T05:30:00Z",
      "notes": "Incident reported by user."
    }
  ],
  "created_at": "2026-08-31T05:30:00Z",
  "resolved_at": null
}
```

---

#### `PATCH /api/incidents/<id>/accept/` — Accept Incident (Person 2)
Used by a responder to claim/accept an incident for their response team.

- **Headers:** `Authorization: Bearer <responder_token>`
- **Request Body (Optional notes / team_id):**
```json
{
  "notes": "EMS Unit 1 dispatched and rolling to scene."
}
```

- **Response (`200 OK`):** Returns updated Incident object with `status: "accepted"`, responder's team assigned, and team status set to `"busy"`.

---

#### `PATCH /api/incidents/<id>/status/` — Update Status (Person 2)
Used by a responder to update incident status (`"in-progress"`, `"resolved"`, `"rejected"`).

- **Headers:** `Authorization: Bearer <responder_token>`
- **Request Body:**
```json
{
  "status": "resolved",
  "notes": "First aid administered. Student transferred to campus infirmary."
}
```

- **Response (`200 OK`):** Returns updated Incident object. If resolved, automatically computes response duration, increments team `cases_handled`, recalculates `avg_response_time`, and returns unit to `"on-duty"`.

---

### 3. Response Teams Endpoints (Person 2 & Person 3)

#### `GET /api/teams/my_team/`
Returns the logged-in responder's assigned response unit.

#### `PATCH /api/teams/update_duty_status/`
Allows responder to toggle duty availability (`"on-duty" | "off-duty" | "busy"`).

- **Request Body:**
```json
{
  "availability_status": "on-duty"
}
```

---

### 4. Admin REST APIs & Analytics (Person 3)

- **`GET /api/admin/analytics/`** — Real-time performance aggregates:
```json
{
  "total_incidents": 22,
  "today_incidents": 4,
  "pending_incidents": 2,
  "active_teams_count": 3,
  "avg_response_time": 4.1,
  "incidents_by_type": {
    "medical": 8,
    "security": 6,
    "fire": 3,
    "harassment": 3,
    "other": 2
  },
  "incidents_by_day": [
    {"date": "Aug 17", "count": 2},
    {"date": "Aug 31", "count": 4}
  ],
  "top_zones_by_incident_count": [
    {"zone": "Hostel & Residential Block", "count": 7},
    {"zone": "North Academic Complex", "count": 6}
  ],
  "team_leaderboard": [
    {
      "id": 2,
      "name": "Campus EMS Unit 1",
      "zone": "Hostel & Residential Block",
      "availability_status": "busy",
      "cases_handled": 18,
      "avg_response_time": 3.2
    }
  ]
}
```

---

## ⚡ REAL-TIME WEBSOCKET CONTRACT

### Connection URL
```
ws://localhost:8000/ws/admin/incidents/
```
*(In production, use `wss://<your-domain>/ws/admin/incidents/`)*

### Events Emitted to WebSocket Clients

#### 1. Initial Connection Handshake
Upon connecting, the server confirms:
```json
{
  "type": "connection_established",
  "message": "Connected to RESQ Live Incident Stream."
}
```

#### 2. `incident.new`
Broadcast immediately when Person 1 submits `POST /api/incidents/`.
```json
{
  "event": "incident.new",
  "data": {
    "id": 24,
    "incident_type": "medical",
    "incident_type_display": "Medical Emergency",
    "description": "Student collapsed during gym workout.",
    "location_lat": 12.9705,
    "location_lng": 77.5930,
    "address": "Sports Complex Gymnasium",
    "status": "pending",
    "status_display": "Pending / Unassigned",
    "reported_by": {
      "id": 7,
      "username": "priya_sharma",
      "phone": "+1-555-0302"
    },
    "assigned_team": null,
    "created_at": "2026-08-31T05:35:10Z"
  }
}
```

#### 3. `incident.status_changed`
Broadcast when Person 2 accepts an incident, updates status, or Admin dispatches a unit.
```json
{
  "event": "incident.status_changed",
  "data": {
    "id": 24,
    "incident_type": "medical",
    "status": "accepted",
    "status_display": "Accepted",
    "assigned_team": {
      "id": 2,
      "name": "Campus EMS Unit 1",
      "zone": "Hostel & Residential Block"
    }
  }
}
```

---

## 🖥️ Server-Rendered Admin Dashboard Pages

| URL Route | Description |
| :--- | :--- |
| `/admin-dashboard/login/` | Admin secure login portal |
| `/admin-dashboard/` | Live Emergency Operations (metric cards, dynamic WebSocket live table feed, active units) |
| `/admin-dashboard/incidents/` | Incident directory with search, filters (Status, Type, Zone), and pagination |
| `/admin-dashboard/incidents/<id>/` | Incident detail, dispatch controls, status reassignment, and timeline log |
| `/admin-dashboard/teams/` | Response team management, availability statuses, add new unit modal |
| `/admin-dashboard/users/` | User directory, role filters, add user modal, block/unblock toggles |
| `/admin-dashboard/analytics/` | Dynamic Chart.js 30-day timeline, donut category chart, speed leaderboard |
| `/admin-dashboard/export-csv/` | Direct CSV file export of all incident records |

---

## 🧪 Testing

To run the automated test suite:
```bash
python manage.py test
```

All 5 test suites cover:
1. User registration & JWT generation
2. JWT login validation & claims
3. Incident reporting by Student (Person 1)
4. Incident accept & resolution by Responder (Person 2)
5. Admin analytics calculations & permissions

---

## 👥 Integrated Team Demo Guide

1. **Start Backend**: `python manage.py runserver 8000`
2. **Person 3**: Open `http://localhost:8000/admin-dashboard/` in browser (login: `admin` / `admin123`). The green pulse indicates "Live Sync Active".
3. **Person 1 (User App)**: Call `POST http://localhost:8000/api/incidents/` with a student JWT token. Watch the new incident instantly appear on Person 3's screen with an audio alert and toast notification!
4. **Person 2 (Responder App)**: Call `PATCH http://localhost:8000/api/incidents/<id>/accept/` or `/status/`. Watch the status badge update from Red (Pending) to Yellow (Accepted) to Green (Resolved) across the entire system in real-time.
