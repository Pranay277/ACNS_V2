# 🏗️ ACNS Backend (Accessible Campus Navigation System)

## 📌 Overview
The ACNS backend is built to handle issue reporting, tracking, and resolution workflows for campus infrastructure problems. It provides REST APIs for users, supervisors, and admins, integrates with Firebase (Auth + Firestore), and ensures structured complaint management — including geo-based duplicate detection, gamification, and localized SMS notifications.

## 🚀 Tech Stack
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication (ID-token verification via Admin SDK)
- **SMS**: TextBee gateway (Android SMS Gateway app)
- **Geolocation**: Haversine distance (shared in `shared/utils/geo.py`)

## 📂 Project Structure
```text
backend/
│
├── main.py                # FastAPI app entry point (mounts all feature routers)
├── requirements.txt       # Dependencies
├── .env.example           # Copy to .env and fill in real values
│
├── core/                  # Global infrastructure (no feature imports)
│   ├── config.py          # Centralized configuration (all constants/env settings)
│   ├── firebase.py        # Firebase Admin SDK initialization (single Firestore handle)
│   └── logging.py         # Optional root logging configuration
│
├── features/              # Vertical slices organized by business capability
│   ├── auth/              # Login, signup, roles & valid languages
│   │   ├── router.py      #   HTTP layer
│   │   ├── service.py     #   Firebase ID-token verification
│   │   └── schemas.py     #   LoginRequest / SignupRequest / UserUpdateRequest
│   ├── profile/           # User profiles keyed by Firebase UID
│   │   └── service.py     #   UID-keyed CRUD, lastLogin, legacy users/ fallback
│   ├── issues/            # Issue CRUD, status workflow, verification
│   │   ├── router.py      #   HTTP layer
│   │   ├── service.py     #   Workflow logic (transactions, points, notifications)
│   │   ├── duplicate_check.py  # Campus-aware duplicate detection
│   │   └── schemas.py     #   IssueCreate / IssueStatusUpdate / VerifyIssue
│   ├── navigation/        # Campus pathfinding + landmark/node listing
│   │   ├── router.py      #   HTTP layer
│   │   ├── service.py     #   Route calculation + nearest-landmark lookup
│   │   ├── graph.py       #   Firestore graph loader + A* engine
│   │   └── schemas.py     #   NavigationRequest
│   ├── gamification/      # Leaderboard, profiles, award points
│   │   ├── router.py      #   HTTP layer
│   │   ├── service.py     #   Points, idempotent history, leaderboard ranks
│   │   └── schemas.py     #   GamificationAward
│   ├── notifications/     # In-app notification fetch + dispatch orchestration
│   │   ├── router.py      #   HTTP layer
│   │   └── service.py     #   In-app writes + assignment SMS dispatch
│   ├── supervisors/       # Admin-managed accounts + supervisor self-profile
│   │   ├── router.py      #   HTTP layer
│   │   ├── service.py     #   Lifecycle ops + department-based issue assignment
│   │   └── schemas.py     #   SupervisorCreate / Update / SelfUpdate / ...
│   └── sms/               # Localized SMS dispatch (provider-swappable)
│       ├── service.py     #   Dispatch abstraction + template resolution
│       ├── provider.py    #   TextBee provider for the Android SMS Gateway
│       └── templates/     #   Localized SMS bodies (registry + fallback)
│           ├── english.py
│           ├── telugu.py
│           └── hindi.py
│
├── shared/                # Code shared across features (feature-agnostic)
│   └── utils/
│       ├── geo.py         # Shared Haversine great-circle distance
│       └── validators.py  # Role / preferred-language validation
│
├── scripts/               # Dev scripts
│   ├── seed_users.py      # Idempotent dev account/role provisioning
│   └── seed_graph.py      # Idempotent campus navigation-graph seeding
│
├── migrations/            # One-time idempotent data backfills
│   ├── migrate_issues.py
│   ├── migrate_duplicate_fields.py
│   ├── migrate_preferred_language.py
│   └── migrate_uid_collections.py   # legacy users/ → role collections (UID)
│
└── tests/                 # Regression suite (python -m pytest tests -q)
```

## ⚙️ Features Implemented
- ✅ Issue creation with image + location
- ✅ Campus-aware duplicate detection (same campus + building + category, ≤ 25 m)
- ✅ Auto-routing (category → department → active supervisor via `features/supervisors/service.py`; legacy `CATEGORY_MAP` fallback in `core/config.py`)
- ✅ UID-based identity (profiles keyed by Firebase UID in `students/`, `supervisors/`, `admins/`; legacy `users/{email}` fallback retained)
- ✅ Supervisor self-service profile (display name / phone / language / campus via `PATCH /api/supervisors/{uid}/profile`)
- ✅ Admin-managed supervisor lifecycle (create / edit / change email / activate / deactivate / delete / reset password)
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
| `GET` | `/profile/{userId}` | Fetch a profile by userId (email or UID) |
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

### 🔹 Supervisors (`/api/supervisors`) — admin-managed (keyed by Firebase UID)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List supervisors (`?includeInactive=true` for disabled) |
| `POST` | `/` | Create supervisor (Auth account + profile, returns temp password) |
| `GET` | `/{uid}` | Fetch a supervisor profile |
| `PATCH` | `/{uid}` | Edit department / phone / language / display name |
| `PATCH` | `/{uid}/profile` | Supervisor self-updates their own profile |
| `POST` | `/{uid}/change-email` | Change the supervisor's login email |
| `POST` | `/{uid}/deactivate` | Disable login + soft-delete profile |
| `POST` | `/{uid}/activate` | Re-enable a disabled supervisor |
| `DELETE` | `/{uid}` | Delete supervisor (blocked while open issues assigned) |
| `POST` | `/{uid}/reset-password` | Reset the Firebase Auth password |

## 🔁 Workflow
1. User reports issue (category, description, image, location)
2. Backend resolves campus + nearest building, checks duplicates (≤ 25 m)
3. Duplicate → merge (unique reporters tracked, priority escalated); otherwise a new issue is created and points awarded
4. Issue auto-assigned via category → department → active supervisor
5. Supervisor gets an in-app notification + localized SMS (per their `preferredLanguage`)
6. Supervisor updates status and uploads proof
7. Admin verifies → closes issue
8. Notifications sent at each step

## 🔐 Authentication & Roles
- **Firebase Authentication** → handles login; the backend verifies the client ID token
- **Firestore** → stores profiles keyed by Firebase UID in role collections: `students/{uid}`, `supervisors/{uid}`, `admins/{uid}`

Example:
```json
{
  "uid": "w0Jh3v...eK9m",
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
2. Place your Firebase Admin SDK JSON at `serviceAccountKey.json` (backend root).

### 🔹 Step 3: Seed (optional, dev only)
```bash
python scripts/seed_users.py    # provisioning roles/profiles
python scripts/seed_graph.py    # seeding the campus navigation graph
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
