# SCIARS - Smart Campus Issue and Resolution System

A full-stack web application for reporting, tracking, and resolving campus infrastructure issues using geolocation, role-based dashboards, gamification, and localized SMS notifications.

## 🏗️ Tech Stack

### Frontend (`ACNS_v2/frontend`)
- **React** (with Vite)
- **Tailwind CSS** for styling
- **Leaflet** for interactive maps
- **Recharts** for analytics dashboards
- **Firebase** for authentication & file storage

### Backend (`ACNS_v2/backend`)
- **FastAPI** (Python)
- **Firebase Admin SDK** for server-side operations (Auth + Firestore)
- **Haversine** formula for duplicate issue detection (shared in `utils/geo.py`)
- **TextBee gateway** for SMS notifications (localized to English / Telugu / Hindi)

## 🚀 Getting Started

### Prerequisites
- Node.js >= 18
- Python >= 3.10
- Firebase project with Firestore, Auth & Storage enabled

### Frontend Setup
```bash
cd ACNS_v2/frontend
npm install
cp .env.example .env        # fill in Firebase + API values
npm run dev
```

### Backend Setup
```bash
cd ACNS_v2/backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # fill in TextBee + frontend URL values
uvicorn main:app --reload
```

## 📁 Project Structure

```
ACNS_v2/
├── frontend/               # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/     # Reusable UI (IssueCard, MapView, Navbars)
│   │   ├── constants/      # Shared UI constants (status styles, languages)
│   │   ├── pages/          # Role-based dashboards & views
│   │   ├── hooks/          # Custom React hooks
│   │   └── services/       # API & Firebase client config
│   └── .env.example        # Env template (VITE_API_URL, VITE_FIREBASE_*)
│
└── backend/                # FastAPI + Python
    ├── routers/            # API endpoints (auth, issues, notifications, navigation, gamification)
    ├── services/           # Core business logic
    ├── providers/          # SMS providers (TextBee / Android gateway)
    ├── templates/sms/      # Localized SMS message bodies
    ├── utils/              # Shared helpers (geo)
    ├── models/             # Pydantic schemas
    ├── config.py           # Centralized configuration
    └── seed_*.py / migrate_*.py   # Idempotent dev seeds & backfills
```

## 👥 Team Roles

| Role | Responsibility |
|------|---------------|
| Frontend Dev | React UI, Tailwind styling, Leaflet maps |
| Backend Dev | FastAPI routes, Firebase integration |
| Full Stack | API integration, authentication flow |
| DevOps | Deployment, CI/CD, environment config |

## 📄 License

This project is for educational purposes.
