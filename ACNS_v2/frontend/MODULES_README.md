# SCIARS Frontend Modules

## Overview

Three isolated, production-ready frontend modules for the Smart Campus Issue Reporting and Automated Resolution System (SCIARS).

## Modules Created

### 1. Interactive Map (`src/components/MapView.jsx`)
- **Technology:** react-leaflet + Leaflet
- **Features:**
  - Color-coded markers by status (Open=Red, In Progress=Yellow, Resolved=Blue, Closed=Green)
  - Interactive popups with issue details
  - Custom markers with professional styling
  - Responsive design
- **API:** Fetches from `GET /api/issues?role=admin`
- **Props:** `issues`, `center`, `zoom`

### 2. Analytics Dashboard (`src/components/AnalyticsDashboard.jsx`)
- **Technology:** Recharts
- **Features:**
  - Open vs Closed Issues (Pie Chart)
  - Top Categories (Horizontal Bar Chart)
  - Top 3 Hotspot Locations (Bar Chart)
  - Average Resolution Time calculation
  - Summary statistics cards
  - All data processing happens in frontend
- **Props:** `issues`
- **Data Processing:**
  - Uses `.filter()`, `.reduce()`, `.map()`
  - Calculates resolution time from closed issues only

### 3. Notification Bell (`src/components/NotificationBell.jsx`)
- **Technology:** React hooks, Axios, TailwindCSS
- **Features:**
  - Polls API every 10 seconds
  - Unread count badge
  - Dropdown notification list
  - Auto "mark as read" on click
  - Relative time formatting
  - Click outside to close
  - Loading and error states
- **API:** Fetches from `GET /api/notifications/{userId}`
- **Props:** `userId`

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── MapView.jsx                 # Interactive map component
│   │   ├── AnalyticsDashboard.jsx      # Analytics dashboard component
│   │   ├── NotificationBell.jsx        # Notification bell component
│   │   └── ... (existing components)
│   ├── pages/
│   │   ├── DashboardAdmin.jsx          # Updated to use modular components
│   │   └── DemoModules.jsx             # Demo page with sample data
│   ├── services/
│   │   └── api.js                      # Updated API service
│   └── data/
│       └── sampleData.js               # Sample data for testing
├── package.json                         # Dependencies already installed
└── tailwind.config.js                  # TailwindCSS configured
```

## Quick Start

1. **Navigate to frontend directory:**
   ```bash
   cd sciars-core/frontend
   ```

2. **Install dependencies (if needed):**
   ```bash
   npm install
   ```

3. **Create .env file:**
   ```
   VITE_API_URL=http://localhost:3000/api
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

5. **Access demo page:**
   Visit `http://localhost:5173/demo` to see all three modules in action with sample data.

## Usage Examples

### Using MapView
```jsx
import MapView from './components/MapView';
import { fetchIssues } from './services/api';

const AdminPage = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      const data = await fetchIssues('admin');
      setIssues(data);
    };
    loadData();
  }, []);

  return <MapView issues={issues} />;
};
```

### Using AnalyticsDashboard
```jsx
import AnalyticsDashboard from './components/AnalyticsDashboard';

const Dashboard = () => {
  return <AnalyticsDashboard issues={issues} />;
};
```

### Using NotificationBell
```jsx
import NotificationBell from './components/NotificationBell';

const Navbar = () => {
  return <NotificationBell userId="user-123" />;
};
```

## API Endpoints Required

### GET /api/issues?role=admin
Returns array of issue objects:
```json
[
  {
    "id": "1",
    "category": "Electrical",
    "description": "Broken light",
    "status": "Open",
    "location": {
      "lat": 17.3850,
      "lng": 78.4867,
      "text": "Main Building"
    },
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T10:00:00Z"
  }
]
```

### GET /api/notifications/{userId}
Returns array of notifications:
```json
[
  {
    "id": "1",
    "title": "Issue Resolved",
    "message": "Your issue has been fixed",
    "read": false,
    "createdAt": "2024-01-15T12:00:00Z"
  }
]
```

### PUT /api/notifications/{notificationId}/read
Optional - marks notification as read

## Features Implemented

### MapView Component
- ✅ Fetches from `/api/issues?role=admin`
- ✅ Color-coded markers by status
- ✅ Popup with category, description, status, location
- ✅ Reusable component
- ✅ Custom Leaflet icons
- ✅ Responsive design

### AnalyticsDashboard Component
- ✅ Pie chart for open vs closed
- ✅ Bar chart for top categories
- ✅ Bar chart for top 3 hotspots
- ✅ Average resolution time display
- ✅ All computation in frontend
- ✅ Uses filter, reduce, map
- ✅ Memoized calculations

### NotificationBell Component
- ✅ Polls every 10 seconds
- ✅ Dropdown UI
- ✅ Unread count badge
- ✅ Highlight unread notifications
- ✅ Clean Tailwind UI
- ✅ Click outside to close
- ✅ Loading/error states

### Code Quality
- ✅ Functional components
- ✅ React hooks
- ✅ Production-ready
- ✅ Well-structured
- ✅ Minimal comments (as requested)
- ✅ Clean separation of concerns
- ✅ Optimized with useMemo
- ✅ Responsive TailwindCSS

## Testing

Visit `/demo` route to see all components with sample data.

Sample data files:
- `src/data/sampleData.js` - Sample issues and notifications

## Dependencies

All required dependencies are already in package.json:
- react-leaflet: ^4.2.1
- leaflet: ^1.9.4
- recharts: ^2.10.0
- axios: ^1.6.0
- react: ^18.2.0
- tailwindcss: ^3.4.0

## Notes

- Components are isolated and won't interfere with backend logic
- All API calls use existing REST endpoints
- No direct Firebase writes (read-only if needed)
- Data transformation happens in frontend
- Clean, modular, reusable code
- Production-ready with error handling

## Support

For questions or issues, refer to:
- `COMPONENTS_README.md` - Detailed component documentation
- `src/pages/DemoModules.jsx` - Working examples
- `src/data/sampleData.js` - Sample data format
