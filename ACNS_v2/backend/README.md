# 🏗️ SCIARS Backend (Smart Campus Issue Reporting System)

## 📌 Overview
The SCIARS backend is built to handle issue reporting, tracking, and resolution workflows for campus infrastructure problems. It provides REST APIs for users, supervisors, and admins, integrates with Firebase services, and ensures structured complaint management.

## 🚀 Tech Stack
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication
- **Storage**: Firebase Storage (handled via frontend)
- **SDK**: Firebase Admin SDK
- **API Type**: REST APIs
- **Geolocation Logic**: Haversine Formula (duplicate detection)

## 📂 Project Structure
```text
backend/
│
├── main.py                # FastAPI app entry point
├── requirements.txt       # Dependencies
│
├── routers/
│   ├── issues.py          # Issue-related APIs
│   └── notifications.py   # Notification APIs
│
├── services/
│   ├── firebase_admin.py  # Firebase initialization
│   ├── duplicate_check.py # Haversine logic
│   └── email_service.py   # Email notifications
│
└── models/
    └── schemas.py         # Request/response validation
```

## ⚙️ Features Implemented
- ✅ Issue creation with image + location
- ✅ Geo-based duplicate detection (within 50m)
- ✅ Auto-routing (category → supervisor)
- ✅ Role-based issue fetching (user/supervisor/admin)
- ✅ Status workflow: Open → In Progress → Resolved → Closed
- ✅ Proof-based resolution (image required)
- ✅ Admin verification system
- ✅ In-app notifications

## 📡 API Endpoints

### 🔹 Issues
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/issues` | Create new issue |
| `GET` | `/api/issues` | Fetch issues (role-based) |
| `PUT` | `/api/issues/{id}/status` | Update issue status |
| `POST` | `/api/issues/{id}/verify` | Admin verification |

### 🔹 Notifications
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notifications/{userId}` | Get user notifications |

## 🧾 Sample Request (Create Issue)
```json
{
  "userId": "user1@gmail.com",
  "category": "Electrical",
  "description": "Light not working",
  "imageUrl": "https://example.com/image.jpg",
  "lat": 17.385,
  "lng": 78.486,
  "locationText": "Library"
}
```

## 🔁 Workflow
1. User reports issue
2. Backend checks duplicates (≤ 50m radius)
3. Auto-assigns supervisor
4. Supervisor updates status
5. Supervisor uploads proof
6. Admin verifies → closes issue
7. Notifications sent at each step

## 🔐 Authentication & Roles
- **Firebase Authentication** → handles login
- **Firestore** → stores roles

Example:
```json
{
  "email": "electrical@campus.edu",
  "role": "supervisor"
}
```

## 🧪 Running the Backend Server

### 🔹 Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### 🔹 Step 2: Setup Firebase
1. Add your Firebase Admin SDK JSON file
2. Configure it inside `firebase_admin.py`

### 🔹 Step 3: Run Server
```bash
uvicorn main:app --reload
```

### 🔹 Step 4: Open API Docs
Go to: http://127.0.0.1:8000/docs
👉 Swagger UI will open
👉 You can test all APIs here

## 🌐 Server Details
- **Runs on**: http://127.0.0.1:8000
- Auto-reload enabled for development
- Handles all API requests from frontend

## ⚠️ Notes
- Frontend uploads images → backend only receives URLs
- Email is used as userId
- Role validation is handled via Firestore
- Duplicate detection is based on real-world distance

## 🏁 Status
- ✔ Backend fully functional
- ✔ Ready for frontend integration
- ✔ Demo-ready

## 💡 Future Improvements
- JWT-based authentication
- Role-based middleware
- Pagination & filtering
- Real-time updates (WebSockets)
- Logging & monitoring
