<div align="center">

# ACNS — Autonomous Campus Navigation System

**Smart campus issue reporting, navigation & resolution platform**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-38BDF8?logo=tailwindcss&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Firestore_%26_Auth-FFCA28?logo=firebase&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet&logoColor=white)

</div>

---

## 📌 Project Overview

ACNS (Autonomous Campus Navigation System) is a **smart campus management platform** that enables students to report campus issues while helping supervisors and administrators manage and resolve them efficiently.

Students can file geolocated complaints (electrical, water, cleanliness, infrastructure, accessibility, safety, transport, environment), track status in real time, and earn gamification points for contributing. Supervisors receive department-routed issues plus localized SMS alerts, update statuses, and attach proof of resolution. Administrators manage the supervisor workforce, verify resolutions, and monitor analytics dashboards.

The platform combines **campus-aware duplicate detection**, an **A\* campus navigation assistant**, **role-based dashboards**, **gamification & leaderboards**, and **multilingual SMS notifications** (English, Telugu, Hindi) — all built on a production-ready, **feature-based architecture** with a **UID-first identity model** backed by Firebase Authentication and Firestore.

---

## ✨ Features

| Feature | Description |
|---|---|
| Student / Supervisor / Admin Authentication | Firebase ID-token based login and registration for all three roles |
| Role-Based Access Control | Separate role collections, dashboards, and issue scoping (user / supervisor / admin) |
| Issue Reporting | Geolocated reports with category, description, and optional image |
| Duplicate Issue Detection | Campus-aware matching (same campus + building + category, ≤ 25 m) with unique-reporter tracking and automatic priority escalation |
| Department Auto-Assignment | Issues routed category → department → active supervisor |
| Status Workflow | `Open → In Progress → Resolved → Closed` with mandatory proof for resolution and admin verification (close / reopen) |
| Campus Navigation | A\* pathfinding with accessibility mode and nearest-landmark resolution on an interactive Leaflet map |
| Supervisor Management | Admin CRUD: create, edit, change email, activate / deactivate, reset password, delete (protected while issues are assigned) |
| Supervisor Self Profile | Supervisors update their own display name, phone, language, and campus |
| Multilingual SMS Notifications | Localized TextBee alerts in English, Telugu, and Hindi based on supervisor preference |
| Gamification | Points for reporting (10), confirming (5), and verified resolutions (20) — idempotent per issue |
| Leaderboard | Ranked top contributors with per-user point histories |
| Notification System | In-app notifications at every workflow step |
| UID-based Identity Management | Profiles keyed by Firebase UID in role collections (`students/{uid}`, `supervisors/{uid}`, `admins/{uid}`) with a legacy `users/{email}` read fallback |
| Feature-Based Backend Architecture | Vertical feature slices (`router` / `service` / `schemas`) with centralized config |

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Vite | Build tool & dev server |
| Tailwind CSS 3 | Styling |
| React Router 6 | Client-side routing |
| Axios | API client |
| Leaflet + React Leaflet | Interactive campus maps |
| Recharts | Analytics dashboards |
| Firebase JS SDK | Client-side authentication |

### Backend
| Technology | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| FastAPI + Uvicorn | REST API server |
| Firebase Admin SDK | Auth verification + Firestore access |
| Pydantic | Request/response validation |

### Database
| Technology | Purpose |
|---|---|
| Firestore (NoSQL) | Primary datastore — role profiles, issues, notifications, campuses, gamification |

### Authentication
| Technology | Purpose |
|---|---|
| Firebase Authentication | Email/password accounts; backend verifies client ID tokens via the Admin SDK |

### SMS
| Technology | Purpose |
|---|---|
| TextBee | Android SMS Gateway — localized English / Telugu / Hindi dispatch |

### Maps
| Technology | Purpose |
|---|---|
| Leaflet (frontend) | Interactive campus map rendering |
| Haversine + campus graph (backend) | Distance checks and A\* pathfinding |

### Deployment-Ready
- Environment-driven configuration (`.env` per service)
- CORS middleware enabled (restrict `allow_origins` to your frontend origin before production)
- Static frontend build (`vite build`) servable from any static host
- Idempotent seed scripts and one-time data migrations

---

## 🏗 Current Project Architecture

The backend follows a **feature-based (vertical-slice) architecture**: each business capability lives in its own folder with a thin HTTP layer, business logic, and validation schemas. Features communicate only through their services, and cross-cutting concerns are isolated in `core/`.

```
backend/
├── core/          # Cross-cutting infrastructure (no feature imports)
│   ├── config.py      # All constants, env settings, and collection names
│   ├── firebase.py    # Firebase Admin SDK initialization (single handle)
│   └── logging.py     # Root logging configuration (LOG_LEVEL)
│
├── features/      # Vertical slices organized by business capability
│   ├── auth/          # Login, signup, roles, valid languages
│   ├── profile/       # UID-keyed user profile service (legacy fallback)
│   ├── issues/        # Issue CRUD, status workflow, duplicate detection
│   ├── navigation/    # A* pathfinding + landmark/node listing
│   ├── gamification/  # Points, idempotent history, leaderboard
│   ├── notifications/ # In-app notification writes + dispatch orchestration
│   ├── supervisors/   # Admin-managed supervisor lifecycle + self-profile
│   └── sms/           # Localized SMS dispatch (English / Telugu / Hindi)
│
├── shared/        # Feature-agnostic helpers
│   └── utils/         # geo.py (Haversine), validators.py
│
├── migrations/    # One-time idempotent backfills (incl. UID migration)
├── scripts/       # Idempotent dev seeds (users, campus navigation graph)
└── tests/         # Pytest regression suite
```

Each `features/*` slice contains:

| File | Responsibility |
|---|---|
| `router.py` | REST endpoints (HTTP layer) |
| `service.py` | Business logic, Firestore access, cross-feature calls |
| `schemas.py` | Pydantic request/response models |

The FastAPI app in `main.py` mounts each feature router under `/api/<feature>` — e.g. `/api/auth`, `/api/issues`, `/api/supervisors`.

---

## 🗄 Firestore Structure

All identity is the **Firebase Auth UID**. Each role's profiles live in its own collection, keyed by uid.

| Collection | Purpose |
|---|---|
| `students/{uid}` | Student profiles — display name, email, campus, role, phone, active flag, timestamps |
| `supervisors/{uid}` | Supervisor profiles — additionally carry `department` (drives auto-assignment) and `preferredLanguage` (drives SMS language) |
| `admins/{uid}` | Admin profiles |
| `issues/` | Issue documents — reporter uid, category, description, status, geolocation, campus + building ids, assigned supervisor, unique `reportCount` / `reportedBy`, priority, proof URL, timestamps |
| `notifications/` | In-app notifications — recipient uid, title, message, issue reference, read state |
| `campuses/` | Campus metadata; each campus has `nodes/` (landmarks + route points) and `edges/` (walkable connections) powering the navigation graph |
| `gamification_users/{uid}` | Gamification profile — total points, issues reported/resolved, display name; subcollection `points_history/{event_key}` for idempotent award auditing |

> The legacy `users/{email}` collection is retained **only** as a rollback/read fallback during the UID-migration window; new writes never go there.

---

## 📸 Screenshots

> Placeholders — replace with real captures from the running app.

| Student Dashboard | Supervisor Dashboard | Admin Panel |
|---|---|---|
| ![Student Dashboard](screenshots/student-dashboard.png) | ![Supervisor Dashboard](screenshots/supervisor-dashboard.png) | ![Admin Panel](screenshots/admin-panel.png) |

| Issue Reporting | Campus Map | Leaderboard |
|---|---|---|
| ![Issue Reporting](screenshots/report-issue.png) | ![Campus Map](screenshots/campus-map.png) | ![Leaderboard](screenshots/leaderboard.png) |

---

## 🚀 Installation

### Prerequisites
- Node.js ≥ 18
- Python ≥ 3.10
- A Firebase project with **Firestore** and **Authentication (Email/Password)** enabled

### Frontend

```bash
cd ACNS_v2/frontend
npm install
cp .env.example .env        # fill in Firebase + API values
npm run dev
```

### Backend

```bash
cd ACNS_v2/backend
python -m venv .venv
.venv\Scripts\activate      # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env        # fill in TextBee + frontend URL values
uvicorn main:app --reload
```

### Firebase Setup
1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com).
2. Enable **Authentication → Email/Password**.
3. Create a **Firestore** database in production mode.
4. Register a **web app** to obtain the client SDK config (used in `frontend/.env`).
5. Download the **service account JSON** from Project Settings → Service accounts and save it as `serviceAccountKey.json` in `backend/` (gitignored).

### TextBee (SMS)
1. Install the **TextBee** app on the Android device that will send SMS and sign in.
2. Copy the device's **API Key** and **Device ID** from the app.
3. Add them to `backend/.env` (`TEXTBEE_API_KEY`, `TEXTBEE_DEVICE_ID`).

---

## ▶️ Running the Project

### Development
- **Backend:** `uvicorn main:app --reload` → `http://localhost:8000` (interactive API docs at `http://localhost:8000/docs`)
- **Frontend:** `npm run dev` → `http://localhost:5173`

### Production

**Backend**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
- Set `FRONTEND_BASE_URL` in `backend/.env` to the production frontend origin (used in SMS issue links).
- Restrict CORS to your production origin in `backend/main.py`.

**Frontend**
```bash
npm run build
```
- Serve the `dist/` output with any static host (e.g., Nginx, Vercel, Netlify).
- Point `VITE_API_URL` at the deployed backend.

---

## 🔐 Environment Variables

### Frontend (`frontend/.env`)
| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Backend API base URL, including `/api` (e.g., `http://localhost:8000/api`) |
| `VITE_FIREBASE_API_KEY` | ✅ | Firebase web API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | ✅ | Firebase auth domain |
| `VITE_FIREBASE_PROJECT_ID` | ✅ | Firebase project id |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | ✅ | Firebase messaging sender id |
| `VITE_FIREBASE_APP_ID` | ✅ | Firebase app id |
| `VITE_FIREBASE_STORAGE_BUCKET` | ⬜ | Optional — not currently used (image uploads are not storage-backed) |

### Backend (`backend/.env`)
| Variable | Required | Description |
|---|---|---|
| `TEXTBEE_API_KEY` | ✅ | TextBee gateway API key |
| `TEXTBEE_DEVICE_ID` | ✅ | TextBee device id |
| `TEXTBEE_BASE_URL` | ⬜ | TextBee API base URL (defaults to `https://api.textbee.dev`) |
| `FRONTEND_BASE_URL` | ✅ | Frontend origin used in SMS issue links (no trailing slash) |
| `LOG_LEVEL` | ⬜ | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default `WARNING`) |
| `ADMIN_SEED_EMAIL` | ⬜ | Optional dev admin account seeded by `scripts/seed_users.py` |
| `ADMIN_SEED_PASSWORD` | ⬜ | Password for the seeded admin |
| `ADMIN_SEED_NAME` | ⬜ | Display name for the seeded admin |

> **File (not env):** Firebase Admin credentials must be placed at `backend/serviceAccountKey.json`.

---

## 🧪 Testing

### Backend — pytest
```bash
cd ACNS_v2/backend
python -m pytest tests -q
```
- Pure-logic tests (geo, SMS templates, validators, navigation graph) run without any Firebase access.
- API-contract tests import the FastAPI app and require `backend/serviceAccountKey.json`; they are **skipped automatically** when it is absent.

### Frontend — build check
```bash
cd ACNS_v2/frontend
npm run build
```
- A successful `vite build` validates JSX, imports, and bundling.

### Manual Verification
1. Register a student and report a geolocated issue.
2. Confirm the issue appears on the supervisor dashboard and triggers an in-app notification.
3. Have a supervisor transition the status and attach proof; verify the student is notified.
4. Admin-verify the resolution to close the issue and award gamification points; check the leaderboard.
5. (Optional) Set a supervisor's SMS language and verify a localized TextBee message.

---

## 📁 Folder Structure

```
ACNS_v2/
├── frontend/                    # React + Vite + Tailwind
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx              # Routes for all role-based pages
│       ├── index.css
│       ├── components/          # IssueCard, MapView, Navbars, bells, charts, camera
│       ├── constants/           # Departments, languages, status styles
│       ├── hooks/               # useAdminNotifications
│       ├── pages/               # Landing, Login/Register, dashboards per role,
│       │                        #   ReportIssue, IssueDetails, UserNavigate,
│       │                        #   Leaderboard, SupervisorManagement, SupervisorProfile
│       └── services/            # api.js (Axios client), firebase.js (Auth config)
│
└── backend/                     # FastAPI + Python
    ├── main.py                  # App entry point — mounts all feature routers
    ├── requirements.txt
    ├── .env.example
    ├── core/                    # config, firebase init, logging
    ├── features/                # auth, profile, issues, navigation, gamification,
    │                            #   notifications, supervisors, sms (+ templates/)
    ├── shared/utils/            # geo.py, validators.py
    ├── scripts/                 # seed_users.py, seed_graph.py
    ├── migrations/              # idempotent backfills incl. UID migration
    └── tests/                   # pytest regression suite
```

---

## 🔮 Future Improvements

- Role-based middleware / authorization decorators on all endpoints
- Real-time issue updates via WebSockets or Firestore listeners
- Pagination & filtering on list endpoints
- Firebase Storage for proof-of-work image uploads
- Push / email notification channel alongside in-app and SMS
- UI localization (English / Telugu / Hindi) to match SMS support
- CI/CD pipeline (GitHub Actions: tests + frontend build) and Docker deployment

---

## 👥 Contributors

| Name | Role |
|---|---|
| <!-- Your Name --> | <!-- e.g., Full-Stack Developer --> |
| <!-- Your Name --> | <!-- e.g., Frontend Developer --> |
| <!-- Your Name --> | <!-- e.g., Backend Developer --> |

---

## 📄 License

This project is for educational purposes.
