# 🏗️ SCIARS Backend (Smart Campus Issue Reporting System)

## 📌 Overview
The SCIARS backend is built to handle issue reporting, tracking, and resolution workflows for campus infrastructure problems. It provides REST APIs for users, supervisors, and admins, integrates with Firebase (Auth + Firestore + Storage), and ensures structured complaint management — including geo-based duplicate detection, gamification, and localized SMS notifications.

## 🚀 Tech Stack
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication (ID-token verification via Admin SDK)
- **Storage**: Firebase Storage (uploads handled by the frontend)
- **SMS**: TextBee gateway (Android SMS Gateway app)
- **Geolocation**: Haversine distance (shared in `utils/geo.py`)

## 📂 Project Structure
```text
backend/
│
├── main.py                # FastAPI app entry point (mounts all routers)
├── config.py              # Centralized configuration (all constants/env settings)
├── requirements.txt       # Dependencies
├── .env.example           # Copy to .env and fill in real values
│
├── routers/               # Thin HTTP layer; business logic lives in services/
│   ├── auth.py            # Login, signup, user profiles, roles & languages
│   ├── issues.py          # Issue CRUD, status workflow, verification
│   ├── notifications.py   # In-app notification fetch
│   ├── navigation.py      # Campus pathfinding + landmark/node listing
│   └── gamification.py    # Leaderboard, profiles, award points
│
├── services/              # Business logic (Firestore mutations live here)
│   ├── firebase_admin.py  # Firebase SDK initialization
│   ├── users.py           # Token verification + profile management
│   ├── duplicate_check.py # Campus-aware duplicate detection
│   ├── navigation.py      # A* pathfinding engine + nearest-landmark lookup
│   ├── gamification.py    # Points, idempotent history, leaderboard ranks
│   ├── notify.py          # Notification orchestrator (in-app + SMS)
│   └── sms_service.py     # SMS dispatch abstraction (provider-swappable)
│
├── providers/
│   └── android_gateway.py # TextBee provider for the Android SMS Gateway
│
├── templates/
│   └── sms/               # Localized SMS message bodies (registry + fallback)
│       ├── english.py
│       ├── telugu.py
│       └── hindi.py
│
├── utils/
│   └── geo.py             # Shared Haversine great-circle distance
│
├── models/
│   └── schemas.py         # Request/response validation
│
├── seed_users.py          # Idempotent dev account/role provisioning
├── seed_graph.py          # Idempotent campus navigation-graph seeding
└── migrate_*.py           # One-time idempotent data backfills
```

## ⚙️ Features Implemented
- ✅ Issue creation with image + location
- ✅ Campus-aware duplicate detection (same campus + building + category, ≤ 25 m)
- ✅ Auto-routing (category → supervisor via `CATEGORY_MAP` in `config.py`)
- ✅ Role-based issue fetching (user/supervisor/admin)
- ✅ Status workflow: Open → In Progress → Resolved → Closed
- ✅ Proof-based resolution (image required for Resolved)
- ✅ Admin verification system
- ✅ In-app notifications
- ✅ Gamification: points, idempotent rewards, ranks, leaderboard
- ✅ Campus navigation: A* pathfinding + accessibility mode
- ✅ Localized SMS notifications (English / Telugu / Hindi) via TextBee

## 📡 API Endpoints

### 🔹 Auth & Users (`/api/auth`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/login` | Verify a Firebase ID token, return/self-heal the profile |
| `POST` | `/signup` | Register a new user profile (idempotent) |
| `GET` | `/profile/{userId}` | Fetch a profile by email (doc id) |
| `GET` | `/uid/{uid}` | Fetch a profile by Firebase Auth uid |
| `GET` | `/users` | List user profiles (active by default) |
| `PATCH` | `/users/{userId}` | Update profile fields (whitelisted) |
| `POST` | `/users/{userId}/deactivate` / `/activate` | Enable / disable an account |
| `GET` | `/valid-roles` | Expose the valid role list |
| `GET` | `/valid-languages` | Expose the supported SMS languages |

### 🔹 Issues (`/api/issues`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/` | Create a new issue (or merge into a duplicate) |
| `GET` | `/` | Fetch issues (role-based: user/supervisor/admin) |
| `GET` | `/{id}` | Fetch a single issue with campus/building display names |
| `PUT` | `/{id}/status` | Update issue status (validated transitions) |
| `POST` | `/{id}/verify` | Admin verification (close / reopen) |

### 🔹 Notifications (`/api/notifications`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/{userId}` | Get in-app notifications for a user |

### 🔹 Navigation (`/api/navigation`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/route` | Calculate the shortest accessible path (A*) |
| `GET` | `/campuses/{campus_id}/nodes` | List landmark nodes for a campus |

### 🔹 Gamification (`/api/gamification`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/leaderboard` | Top users by total points |
| `GET` | `/user/{userId}` | Gamification profile + rank |
| `POST` | `/award` | Award points (idempotent per issue) |

## 🔁 Workflow
1. User reports issue (category, description, image, location)
2. Backend resolves campus + nearest building, checks duplicates (≤ 25 m)
3. Duplicate → merge (unique reporters tracked, priority escalated); otherwise a new issue is created and points awarded
4. Issue auto-assigned to the category supervisor
5. Supervisor gets an in-app notification + localized SMS (per their `preferredLanguage`)
6. Supervisor updates status and uploads proof
7. Admin verifies → closes issue
8. Notifications sent at each step

## 🔐 Authentication & Roles
- **Firebase Authentication** → handles login; the backend verifies the client ID token
- **Firestore** → stores profiles under `users/{email}` (email is the userId convention)

Example:
```json
{
  "email": "electrical@campus.edu",
  "role": "supervisor",
  "preferredLanguage": "en"
}
```

## 🧪 Running the Backend Server

### 🔹 Step 1: Create a virtual environment and install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 🔹 Step 2: Configure environment
1. Copy `.env.example` to `.env` and fill in `TEXTBEE_API_KEY`, `TEXTBEE_DEVICE_ID`, and `FRONTEND_BASE_URL`.
2. Place your Firebase Admin SDK JSON at `services/serviceAccountKey.json`.

### 🔹 Step 3: Seed (optional, dev only)
```bash
python seed_users.py    # provisioning roles/profiles
python seed_graph.py    # seeding the campus navigation graph
```

### 🔹 Step 4: Run Server
```bash
uvicorn main:app --reload
```

### 🔹 Step 5: Open API Docs
Go to: http://127.0.0.1:8000/docs
👉 Swagger UI — test all APIs here.

## 🌐 Server Details
- **Runs on**: http://127.0.0.1:8000
- Auto-reload enabled for development
- Handles all API requests from the frontend

## 💡 Future Improvements
- Role-based middleware / authorization decorators
- Pagination & filtering on list endpoints
- Real-time updates (WebSockets / Firestore listeners)
- Structured logging & monitoring
