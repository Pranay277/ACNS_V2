# ACNS_V2 — Final Project Report

## Project Overview

**ACNS_V2** (Accessible Campus Navigation System v2) is a full-stack web application that merges two systems:
- **SCIARS** — Smart Campus Issue Reporting and Automated Resolution System
- **ACNS** — Accessibility-focused Campus Navigation System

The integrated product allows students and staff to **report campus infrastructure issues** and **navigate between buildings** via accessible, wheelchair-friendly routes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TailwindCSS, Leaflet, Recharts, Axios |
| Backend | FastAPI (Python), Uvicorn |
| Database | Google Firestore (NoSQL) |
| Auth | Firebase Authentication |
| Storage | Firebase Storage |
| Notifications | Twilio WhatsApp API |

---

## Repository Structure

```
E:\ACNS\
└── ACNS_v2/
    ├── backend/
    │   ├── main.py                      ← FastAPI entry point
    │   ├── seed_graph.py                ← [NEW] One-time Firestore graph seeder
    │   ├── requirements.txt
    │   ├── .env                         ← Secrets (not in git)
    │   ├── models/
    │   │   └── schemas.py               ← Pydantic models (incl. NavigationRequest)
    │   ├── routers/
    │   │   ├── issues.py                ← Issue CRUD + duplicate detection
    │   │   ├── notifications.py         ← User notification feed
    │   │   └── navigation.py            ← [NEW] A* route calculation endpoint
    │   └── services/
    │       ├── firebase_admin.py        ← Firestore client init
    │       ├── twilio_service.py        ← WhatsApp notifications
    │       ├── duplicate_check.py       ← Haversine duplicate detection
    │       └── navigation.py            ← [NEW] A* algorithm engine
    └── frontend/
        ├── .env                         ← Frontend env vars (not in git)
        └── src/
            ├── App.jsx                  ← React Router config
            ├── pages/
            │   ├── Login.jsx
            │   ├── Register.jsx
            │   ├── ReportIssue.jsx
            │   ├── DashboardUser.jsx
            │   ├── DashboardSupervisor.jsx
            │   ├── DashboardAdmin.jsx
            │   ├── AdminIssues.jsx
            │   ├── Leaderboard.jsx
            │   └── UserNavigate.jsx     ← [UPDATED] Navigation UI with A* integration
            └── components/
                ├── MapView.jsx
                ├── NavbarUser.jsx
                ├── NotificationBell.jsx
                └── ...
```

---

## Features Implemented

### ✅ Core SCIARS Features (Migrated)
| Feature | Status | Notes |
|---|---|---|
| User Registration / Login | ✅ Working | Firebase Auth |
| Issue Reporting with Map Pin | ✅ Working | Leaflet + Firestore |
| Smart Duplicate Detection | ✅ Working | Haversine 120m radius merge |
| Auto-Priority Escalation | ✅ Working | 5+ reports → High, 10+ → Critical |
| WhatsApp Supervisor Notification | ✅ Working | Twilio integration |
| User Dashboard (My Issues) | ✅ Working | Status tracking |
| Supervisor Dashboard | ✅ Working | Claim & resolve issues |
| Admin Dashboard | ✅ Working | Full issue management |
| Notification Bell | ✅ Working | 10s polling from Firestore |
| Leaderboard | ✅ Working | Top reporters |

### ✅ NEW Navigation Features (Integrated from ACNS)
| Feature | Status | Notes |
|---|---|---|
| Campus-Agnostic Architecture | ✅ Implemented | `campusId` subcollection design |
| Firestore Graph Schema | ✅ Designed | `nodes` + `edges` subcollections |
| Firestore Seeding Script | ✅ Created | `seed_graph.py` |
| A* Pathfinding Engine | ✅ Implemented | `services/navigation.py` |
| Accessibility Mode Filter | ✅ Implemented | Skips `is_accessible=False` edges |
| Navigation REST API | ✅ Implemented | `POST /api/navigation/route` |
| Route Polyline on Map | ✅ Implemented | Green (standard) / Blue dashed (accessible) |
| Accessibility Toggle UI | ✅ Implemented | Toggle switch in navigation bar |
| Route Summary Card | ✅ Implemented | Distance + path node IDs shown |
| Multi-Campus Support | ✅ Implemented | Methodist (seeded) + OU (data pending) |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/issues/` | Create a new issue report |
| GET | `/api/issues/` | List all issues (with filters) |
| PATCH | `/api/issues/{id}/status` | Update issue status |
| GET | `/api/notifications/{userId}` | Get user notifications |
| **POST** | **`/api/navigation/route`** | **Calculate A* route** |
| GET | `/api/navigation/campuses/{id}/nodes` | Get landmark nodes for a campus |

---

## How to Run

### Backend
```powershell
cd E:\ACNS\ACNS_v2\backend
.\acnsv2\Scripts\Activate
pip install -r requirements.txt uvicorn twilio python-dotenv
uvicorn main:app --reload
# Runs on: http://127.0.0.1:8000
# API docs: http://127.0.0.1:8000/docs
```

### Seed the Navigation Graph (one-time only)
```powershell
# With venv still active, from the backend folder:
python seed_graph.py
```

### Frontend
```powershell
cd E:\ACNS\ACNS_v2\frontend
npm install --legacy-peer-deps
npm run dev
# Runs on: http://localhost:5173
```

---

## Environment Variables Required

### `backend/.env`
```
FIREBASE_CREDENTIALS_PATH=services/serviceAccountKey.json
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
SUPERVISOR_WHATSAPP_TO=whatsapp:+91XXXXXXXXXX
```

### `frontend/.env`
```
VITE_API_URL=http://127.0.0.1:8000/api
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

---

## Navigation Test Case

To verify the accessibility engine is working:

1. Select **Methodist College** in the navigation page.
2. Set **Start: D Block**, **End: C Block**.
3. Click **Calculate Route** (accessibility OFF).
   - Expected: Short direct path `d-block → c-block` via stairs (~70m).
4. Toggle **♿ Accessible Route** ON, click **Calculate Route** again.
   - Expected: Longer rerouted path `d-block → central-junction → e-block → south-junction → c-block` (~160m).

> [!IMPORTANT]
> You must run `python seed_graph.py` **once** before testing navigation. Without seeded graph data, the engine returns 404.

---

## Known Limitations & Future Roadmap

| Item | Status | Notes |
|---|---|---|
| Methodist Campus coordinates | ⚠️ Placeholder | Junction nodes need GPS verification |
| Osmania University graph | ❌ Pending | No coordinates collected yet |
| Navigation page route in App.jsx | ⚠️ Verify | Confirm `/navigate` route exists |
| Destination issue alerts | ❌ Not yet | Warn user if active issues exist at destination |
| Gamification (points/leaderboard) | 🔄 Partial | Leaderboard page exists, point-awarding logic TBD |
| Production Firebase security rules | ❌ Pending | Currently in test/open mode |
| HTTPS / deployment | ❌ Pending | Local development only |
