# SCIARS Frontend Modules Usage Guide

This guide explains how to use the three frontend modules for the SCIARS project.

## Components Overview

### 1. MapView Component
Interactive map displaying campus issues with color-coded markers.

**Location:** `src/components/MapView.jsx`

**Usage:**
```jsx
import MapView from './components/MapView';
import { fetchIssues } from './services/api';
import { useEffect, useState } from 'react';

const AdminDashboard = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    const loadIssues = async () => {
      const data = await fetchIssues('admin');
      setIssues(data);
    };
    loadIssues();
  }, []);

  return (
    <div>
      <h2>Campus Issues Map</h2>
      <MapView issues={issues} />
    </div>
  );
};
```

**Features:**
- Color-coded markers by status (Red=Open, Yellow=In Progress, Blue=Resolved, Green=Closed)
- Interactive popups with issue details
- Custom markers using Leaflet
- Responsive design

---

### 2. AnalyticsDashboard Component
Analytics dashboard with charts and statistics computed entirely on the frontend.

**Location:** `src/components/AnalyticsDashboard.jsx`

**Usage:**
```jsx
import AnalyticsDashboard from './components/AnalyticsDashboard';
import { fetchIssues } from './services/api';
import { useEffect, useState } from 'react';

const Dashboard = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    const loadIssues = async () => {
      const data = await fetchIssues('admin');
      setIssues(data);
    };
    loadIssues();
  }, []);

  return (
    <div>
      <h2>Analytics Dashboard</h2>
      <AnalyticsDashboard issues={issues} />
    </div>
  );
};
```

**Features:**
- Open vs Closed Issues (Pie Chart)
- Top Categories (Horizontal Bar Chart)
- Top 3 Hotspot Locations (Bar Chart)
- Average Resolution Time (calculated from closed issues)
- Summary cards with key metrics
- All data processing happens in the frontend

---

### 3. NotificationBell Component
Real-time notification system with polling.

**Location:** `src/components/NotificationBell.jsx`

**Usage:**
```jsx
import NotificationBell from './components/NotificationBell';

const Navbar = () => {
  const userId = 'current-user-id'; // Get from auth context

  return (
    <nav className="flex justify-between items-center p-4 bg-white shadow">
      <div className="text-xl font-bold">SCIARS</div>
      <div className="flex items-center space-x-4">
        <NotificationBell userId={userId} />
        {/* Other nav items */}
      </div>
    </nav>
  );
};
```

**Features:**
- Polls API every 10 seconds
- Unread notification badge
- Dropdown UI with notification list
- Automatic "mark as read" on click
- Time formatting (relative: "5m ago", "2h ago", etc.)
- Click outside to close
- Loading and error states

---

## API Endpoints

The components expect the following API endpoints:

### GET /api/issues?role=admin
Returns array of issues:
```json
[
  {
    "id": "1",
    "category": "Electrical",
    "description": "Broken street light",
    "status": "Open",
    "location": {
      "lat": 17.3850,
      "lng": 78.4867,
      "text": "Main Building Entrance"
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
    "message": "Your reported issue has been resolved",
    "read": false,
    "timestamp": "2024-01-15T12:00:00Z",
    "createdAt": "2024-01-15T12:00:00Z"
  }
]
```

### PUT /api/notifications/{notificationId}/read
Marks notification as read (optional - will work without it but won't persist)

---

## Environment Variables

Create `.env` file in `frontend/` directory:
```
VITE_API_URL=http://localhost:3000/api
```

---

## Styling

All components use TailwindCSS classes and are fully responsive. The components are self-contained and will work with any layout that has Tailwind configured.

---

## Data Processing (Frontend Only)

All analytics calculations happen in the browser:

1. **Issue Counts:** Uses `.filter()` to separate open/closed issues
2. **Category Aggregation:** Uses `.reduce()` to count issues per category
3. **Location Aggregation:** Uses `.reduce()` to count issues per location
4. **Resolution Time:** Calculates time difference between `createdAt` and `updatedAt` for closed issues

---

## Performance Optimizations

1. **MapView:** Uses `useMemo` to transform issue data before rendering
2. **AnalyticsDashboard:** Uses `useMemo` to compute all statistics once per update
3. **NotificationBell:** 
   - Uses `useRef` for dropdown reference to avoid re-renders
   - Polls efficiently with 10-second intervals
   - Updates only changed notifications

---

## Customization

### Changing Map Colors
Edit the `statusColors` object in `MapView.jsx`:
```javascript
const statusColors = {
  Open: '#ef4444',
  'In Progress': '#eab308',
  Resolved: '#3b82f6',
  Closed: '#22c55e',
};
```

### Changing Polling Interval
Edit the interval in `NotificationBell.jsx`:
```javascript
setInterval(fetchNotifications, 10000); // Change 10000 to desired milliseconds
```

### Changing Default Map Center
Pass `center` prop to MapView:
```jsx
<MapView issues={issues} center={[40.7128, -74.0060]} zoom={15} />
```

---

## Testing

To test with mock data, you can pass arrays directly:

```jsx
const mockIssues = [
  {
    id: '1',
    category: 'Electrical',
    description: 'Broken light',
    status: 'Open',
    location: { lat: 17.3850, lng: 78.4867, text: 'Library' }
  }
];

<MapView issues={mockIssues} />
<AnalyticsDashboard issues={mockIssues} />
```

---

## Dependencies

Required npm packages (already in package.json):
- react-leaflet: ^4.2.1
- leaflet: ^1.9.4
- recharts: ^2.10.0
- axios: ^1.6.0

---

## Troubleshooting

### Map not displaying?
- Ensure Leaflet CSS is imported: `import 'leaflet/dist/leaflet.css'`
- Check browser console for errors
- Verify map container has explicit height

### Charts not rendering?
- Ensure recharts components are properly imported
- Check if data array is not empty
- Verify data format matches expected structure

### Notifications not loading?
- Verify API endpoint is accessible
- Check network tab for 404 errors
- Ensure userId is properly passed

---

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.
