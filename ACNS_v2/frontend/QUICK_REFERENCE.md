# Quick Reference - SCIARS Frontend Modules

## Component Quick Reference

### MapView.jsx
```
┌─────────────────────────────────────────┐
│         Interactive Campus Map          │
│  ┌─────────────────────────────────┐    │
│  │    🔴 Open Issues (Red)         │    │
│  │    🟡 In Progress (Yellow)      │    │
│  │    🔵 Resolved (Blue)           │    │
│  │    🟢 Closed (Green)            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Click marker → Popup with:            │
│  • Category                            │
│  • Description                         │
│  • Status (color-coded)                │
│  • Location text                       │
└─────────────────────────────────────────┘

Usage: <MapView issues={issues} />
```

### AnalyticsDashboard.jsx
```
┌─────────────────────────────────────────┐
│  Stats Cards                            │
│  ┌────────┐ ┌────────┐ ┌────────┐     │
│  │ Total  │ │ Open   │ │Closed  │     │
│  │  10    │ │   3    │ │   7    │     │
│  └────────┘ └────────┘ └────────┘     │
│  ┌──────────────────────────┐          │
│  │ Avg Resolution: 24.5 hrs │          │
│  └──────────────────────────┘          │
│                                         │
│  ┌─────────────┐ ┌─────────────┐       │
│  │  Pie Chart  │ │   Bar       │       │
│  │ Open/Closed │ │   Categories│       │
│  └─────────────┘ └─────────────┘       │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │     Top 3 Hotspot Locations     │    │
│  │     (Bar Chart)                 │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

Usage: <AnalyticsDashboard issues={issues} />
```

### NotificationBell.jsx
```
┌─────────────────────────────────────────┐
│  [Bell Icon] 🔔 Badge: 2                │
│                                         │
│  When clicked:                          │
│  ┌─────────────────────────────────┐    │
│  │ Notifications            Loading│    │
│  ├─────────────────────────────────┤    │
│  │ 🟢 New Issue        5m ago  ●   │    │ ← Unread (blue bg)
│  │ 🟢 Issue Resolved   30m ago ●   │    │ ← Unread (blue bg)
│  │ ⚪ Status Update      2h ago     │    │ ← Read
│  │ ⚪ New Comment        5h ago    │    │ ← Read
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘

Usage: <NotificationBell userId="user-123" />
```

---

## Integration Example

```jsx
// App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardAdmin from './pages/DashboardAdmin';
import DemoModules from './pages/DemoModules';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/dashboard/admin" element={<DashboardAdmin />} />
        <Route path="/demo" element={<DemoModules />} />
        {/* ... */}
      </Routes>
    </BrowserRouter>
  );
}
```

```jsx
// DashboardAdmin.jsx
import MapView from '../components/MapView';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import NotificationBell from '../components/NotificationBell';
import { fetchIssues } from '../services/api';

const DashboardAdmin = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    fetchIssues('admin').then(setIssues);
  }, []);

  return (
    <div>
      <NotificationBell userId="admin" />
      <MapView issues={issues} />
      <AnalyticsDashboard issues={issues} />
    </div>
  );
};
```

---

## API Format Reference

### Issue Object
```javascript
{
  id: '1',
  category: 'Electrical',
  description: 'Broken street light',
  status: 'Open',  // 'Open' | 'In Progress' | 'Resolved' | 'Closed'
  location: {
    lat: 17.3850,
    lng: 78.4867,
    text: 'Main Building Entrance'
  },
  createdAt: '2024-01-15T10:00:00Z',
  updatedAt: '2024-01-15T10:00:00Z'
}
```

### Notification Object
```javascript
{
  id: '1',
  title: 'New Issue Reported',
  message: 'Electrical issue near entrance',
  read: false,
  createdAt: '2024-01-15T12:00:00Z'
}
```

---

## Color Codes

| Status | Color | Hex Code |
|--------|-------|----------|
| Open | Red | #ef4444 |
| In Progress | Yellow | #eab308 |
| Resolved | Blue | #3b82f6 |
| Closed | Green | #22c55e |

---

## File Locations

```
src/
├── components/
│   ├── MapView.jsx              ← Interactive map
│   ├── AnalyticsDashboard.jsx   ← Charts & stats
│   └── NotificationBell.jsx     ← Notifications
├── pages/
│   ├── DashboardAdmin.jsx       ← Uses all modules
│   └── DemoModules.jsx          ← Demo with sample data
├── services/
│   └── api.js                   ← API functions
└── data/
    └── sampleData.js            ← Sample data
```

---

## Routes

- `/dashboard/admin` - Full admin dashboard
- `/demo` - Demo page with sample data

---

## Quick Test

1. Run: `npm run dev`
2. Visit: `http://localhost:5173/demo`
3. See all three modules with sample data

---

## Dependencies

```json
"react-leaflet": "^4.2.1",
"leaflet": "^1.9.4",
"recharts": "^2.10.0",
"axios": "^1.6.0"
```

All installed in package.json ✅

---

## Key Features Checklist

### MapView ✅
- [x] react-leaflet integration
- [x] Color-coded markers
- [x] Popup details
- [x] Custom icons
- [x] Responsive design

### AnalyticsDashboard ✅
- [x] Recharts charts
- [x] Open/Closed pie chart
- [x] Category bar chart
- [x] Hotspot bar chart
- [x] Resolution time
- [x] Stats cards
- [x] Frontend computation

### NotificationBell ✅
- [x] 10-second polling
- [x] Dropdown UI
- [x] Unread badge
- [x] Highlight unread
- [x] Mark as read
- [x] Time formatting
- [x] Error handling

---

## Support

- Full docs: `COMPONENTS_README.md`
- Overview: `MODULES_README.md`
- Summary: `IMPLEMENTATION_SUMMARY.md`
- Demo: `/demo` route
