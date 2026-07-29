# SCIARS - Smart City Issue and Resolution System

A full-stack web application for reporting, tracking, and resolving civic issues using geolocation, role-based dashboards, and real-time notifications.

## 🏗️ Tech Stack

### Frontend
- **React** (with Vite)
- **Tailwind CSS** for styling
- **Leaflet** for interactive maps
- **Recharts** for analytics dashboards
- **Firebase** for authentication & file storage

### Backend
- **FastAPI** (Python)
- **Firebase Admin SDK** for server-side operations
- **Haversine** formula for duplicate issue detection
- **SMTP / Nodemailer** for email notifications

## 🚀 Getting Started

### Prerequisites
- Node.js >= 18
- Python >= 3.10
- Firebase project with Firestore & Auth enabled

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📁 Project Structure

```
sciars-core/
├── frontend/          # React + Vite + Tailwind
│   └── src/
│       ├── components/   # Reusable UI (IssueCard, MapView, Navbar)
│       ├── pages/        # Role-based dashboards & views
│       └── services/     # API & Firebase client config
│
└── backend/           # FastAPI + Python
    ├── routers/          # API endpoints
    ├── services/         # Core business logic
    └── models/           # Pydantic schemas
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
