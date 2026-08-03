import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import NavbarUser from "../components/NavbarUser";
import { getIssues } from "../services/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

const CATEGORIES = ["Infrastructure", "Electrical", "Cleanliness", "Safety", "Transport", "Environment"];

const statusColors = {
  Open:          { bg: '#ef4444', border: '#b91c1c' },
  'In Progress': { bg: '#f59e0b', border: '#d97706' },
  Resolved:      { bg: '#22c55e', border: '#16a34a' },
};

const createBallPin = (status) => {
  const { bg, border } = statusColors[status] || { bg: '#6366f1', border: '#4338ca' };
  return L.divIcon({
    className: '',
    html: `<div style="display:flex;flex-direction:column;align-items:center;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.35));"><div style="width:22px;height:22px;border-radius:50%;background:${bg};border:3px solid ${border};box-shadow:0 0 0 2px rgba(255,255,255,0.7);"></div><div style="width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid ${border};margin-top:-2px;"></div></div>`,
    iconSize: [22, 32],
    iconAnchor: [11, 32],
    popupAnchor: [0, -34],
  });
};

const createStartPin = () => L.divIcon({
  className: '',
  html: `<div style="display:flex;flex-direction:column;align-items:center;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.4));"><div style="width:26px;height:26px;border-radius:50%;background:#22c55e;border:4px solid #16a34a;box-shadow:0 0 0 3px rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold;">S</div><div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:10px solid #16a34a;margin-top:-2px;"></div></div>`,
  iconSize: [26, 38],
  iconAnchor: [13, 38],
  popupAnchor: [0, -40],
});

const createEndPin = () => L.divIcon({
  className: '',
  html: `<div style="display:flex;flex-direction:column;align-items:center;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.4));"><div style="width:26px;height:26px;border-radius:50%;background:#ef4444;border:4px solid #b91c1c;box-shadow:0 0 0 3px rgba(255,255,255,0.9);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold;">E</div><div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:10px solid #b91c1c;margin-top:-2px;"></div></div>`,
  iconSize: [26, 38],
  iconAnchor: [13, 38],
  popupAnchor: [0, -40],
});

const proximityThreshold = 0.002;

const getCategoryCounts = (issues, lat, lng) => {
  const nearby = issues.filter((i) => {
    if (!i.location?.lat || !i.location?.lng) return false;
    return Math.abs(i.location.lat - lat) < proximityThreshold && Math.abs(i.location.lng - lng) < proximityThreshold;
  });
  const counts = {};
  CATEGORIES.forEach((cat) => { counts[cat] = 0; });
  nearby.forEach((i) => {
    const cat = i.category || "Other";
    if (counts[cat] !== undefined) counts[cat]++;
  });
  return counts;
};

function FlyTo({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, zoom ?? 16, { duration: 1.5 });
  }, [center, zoom, map]);
  return null;
}

const defaultCenter = [17.4126, 78.5247];

const CAMPUS_DATA = {
  "OU College": {
    campusId: "osmania",
    center: [17.4126, 78.5247],
    zoom: 15,
    boundary: [
      [17.4240, 78.5100],
      [17.4240, 78.5400],
      [17.4080, 78.5450],
      [17.4050, 78.5380],
      [17.4070, 78.5080],
    ],
    boundaryColor: '#dc2626',
    locations: [
      { id: "arts", name: "Arts College", lat: 17.418974, lng: 78.526596 },
      { id: "engineering", name: "College of Engineering", lat: 17.414640, lng: 78.525180 },
      { id: "science", name: "University College of Science", lat: 17.405640, lng: 78.453610 },
      { id: "tech", name: "University College of Technology", lat: 17.410510, lng: 78.528440 },
      { id: "law", name: "University College of Law", lat: 17.411120, lng: 78.526980 },
      { id: "commerce", name: "Commerce & Business Management", lat: 17.417220, lng: 78.525240 },
      { id: "library", name: "Main Library", lat: 17.416230, lng: 78.524820 },
      { id: "tagore", name: "Tagore Auditorium", lat: 17.411690, lng: 78.529420 },
    ],
  },
  "Methodist College": {
    campusId: "methodist",
    center: [17.39181094222161, 78.47856891694526],
    zoom: 18,
    boundary: [
      [17.39225, 78.47835],
      [17.39225, 78.47900],
      [17.39100, 78.47965],
      [17.39050, 78.47930],
      [17.39050, 78.47850],
    ],
    boundaryColor: '#2563eb',
    locations: [
      { id: "a-block", name: "A Block", lat: 17.39187669271827, lng: 78.478495032659 },
      { id: "b-block", name: "B Block", lat: 17.392086641041143, lng: 78.47893504574874 },
      { id: "c-block", name: "C Block", lat: 17.390641250098902, lng: 78.47929130229612 },
      { id: "d-block", name: "D Block", lat: 17.39157537237309, lng: 78.47870037180208 },
      { id: "e-block", name: "E Block", lat: 17.39128050018839, lng: 78.47951459282437 },
    ],
  },
};

export default function UserNavigate() {
  const [issues, setIssues] = useState([]);
  const [selectedCollege, setSelectedCollege] = useState("");
  const [startId, setStartId] = useState("");
  const [endId, setEndId] = useState("");
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [routeResult, setRouteResult] = useState(null);
  const [mapCenter, setMapCenter] = useState(null);
  const [mapZoom, setMapZoom] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await getIssues({});
        const data = Array.isArray(res.data) ? res.data : [];
        setIssues(data.filter((i) => i.location?.lat && i.location?.lng));
      } catch {
        setIssues([]);
      }
    })();
  }, []);

  const campus = selectedCollege ? CAMPUS_DATA[selectedCollege] : null;
  const locations = campus ? campus.locations : [];
  const activeBoundary = campus ? campus.boundary : null;
  const activeBoundaryOptions = campus
    ? { color: campus.boundaryColor, weight: 3, dashArray: '10, 10', fillColor: campus.boundaryColor, fillOpacity: 0.08 }
    : null;

  useEffect(() => {
    if (!campus) return;
    setMapCenter(campus.center);
    setMapZoom(campus.zoom);
    setRouteResult(null);
  }, [selectedCollege, campus]);

  const handleCalculate = async () => {
    if (!selectedCollege) { setError("Select a college first."); return; }
    if (!startId || !endId) { setError("Select both start and end locations."); return; }
    if (startId === endId) { setError("Start and end must be different."); return; }

    setError("");
    setLoading(true);
    setRouteResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/navigation/route`, {
        campus_id: campus.campusId,
        start_node: startId,
        end_node: endId,
        accessibility_mode: accessibilityMode,
      });
      setRouteResult(response.data);
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to calculate route. Please try again.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <NavbarUser />

      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-wrap items-end gap-3 bg-gray-50 rounded-lg p-3">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">College</label>
            <select
              value={selectedCollege}
              onChange={(e) => { setSelectedCollege(e.target.value); setStartId(""); setEndId(""); setError(""); setRouteResult(null); }}
              className="w-full px-4 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white min-w-[180px]"
            >
              <option value="">Select college</option>
              <option value="OU College">OU College</option>
              <option value="Methodist College">Methodist College</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Start</label>
            <select
              value={startId}
              onChange={(e) => { setStartId(e.target.value); setError(""); setRouteResult(null); }}
              className="w-full px-4 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
              disabled={!selectedCollege}
            >
              <option value="">Select start</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>{loc.name}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">End</label>
            <select
              value={endId}
              onChange={(e) => { setEndId(e.target.value); setError(""); setRouteResult(null); }}
              className="w-full px-4 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
              disabled={!selectedCollege}
            >
              <option value="">Select end</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>{loc.name}</option>
              ))}
            </select>
          </div>

          {/* Accessibility Mode Toggle */}
          <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-md">
            <span className="text-sm font-medium text-blue-800 whitespace-nowrap">♿ Accessible Route</span>
            <button
              onClick={() => { setAccessibilityMode(!accessibilityMode); setRouteResult(null); }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                accessibilityMode ? 'bg-blue-600' : 'bg-gray-300'
              }`}
              id="accessibility-toggle"
              aria-label="Toggle accessibility mode"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                  accessibilityMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <button
            onClick={handleCalculate}
            disabled={!startId || !endId || loading}
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm whitespace-nowrap"
          >
            {loading ? "Calculating..." : "Calculate Route"}
          </button>
        </div>

        {error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Route Result Summary */}
        {routeResult && routeResult.success && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-semibold text-green-800">
              ✅ Route found — {routeResult.total_distance_meters}m
              {routeResult.accessibility_mode && <span className="ml-2 text-blue-700 font-normal">♿ Wheelchair friendly</span>}
            </p>
            <p className="text-xs text-green-600 mt-1">
              Path: {routeResult.path_node_ids.join(" → ")}
            </p>
          </div>
        )}

        {routeResult && !routeResult.success && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
            ⚠️ {routeResult.message}
          </div>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6 w-full">
        <div className="relative w-full h-[520px] rounded-xl overflow-hidden shadow-md border border-gray-200">
          <MapContainer center={defaultCenter} zoom={15} className="w-full h-full" scrollWheelZoom={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Polygon positions={CAMPUS_DATA["OU College"].boundary} pathOptions={{ color: '#dc2626', weight: 3, dashArray: '10, 10', fillColor: '#dc2626', fillOpacity: 0.08 }} />
            <Polygon positions={CAMPUS_DATA["Methodist College"].boundary} pathOptions={{ color: '#2563eb', weight: 3, dashArray: '10, 10', fillColor: '#2563eb', fillOpacity: 0.08 }} />
            <FlyTo center={mapCenter} zoom={mapZoom} />

            {/* Route Polyline */}
            {routeResult?.success && routeResult.path.length > 1 && (
              <Polyline
                positions={routeResult.path}
                pathOptions={{
                  color: accessibilityMode ? '#2563eb' : '#16a34a',
                  weight: 5,
                  opacity: 0.85,
                  dashArray: accessibilityMode ? '10, 5' : null,
                }}
              />
            )}

            {issues.map((issue, index) => (
              <Marker
                key={issue.id || index}
                position={[issue.location.lat, issue.location.lng]}
                icon={createBallPin(issue.status)}
              >
                <Popup>
                  <div style={{ minWidth: '160px' }}>
                    <p style={{ fontWeight: 700, fontSize: '13px', marginBottom: '4px' }}>
                      {issue.category || 'Issue'}
                    </p>
                    <p style={{ fontSize: '12px', color: '#555', marginBottom: '4px' }}>
                      {issue.description}
                    </p>
                    <p style={{ fontSize: '11px', color: '#888' }}>
                      📍 {issue.location?.text || ''}
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {startId && locations.filter((l) => l.id === startId).map((loc) => {
              const counts = getCategoryCounts(issues, loc.lat, loc.lng);
              return (
                <Marker key={loc.id} position={[loc.lat, loc.lng]} icon={createStartPin()}>
                  <Popup>
                    <div style={{ minWidth: '180px' }}>
                      <p style={{ fontWeight: 700, fontSize: '14px', marginBottom: '6px', color: '#16a34a' }}>🟢 {loc.name} (Start)</p>
                      <p style={{ fontSize: '11px', color: '#888', marginBottom: '6px' }}>Issues near here:</p>
                      {CATEGORIES.map((cat) => (
                        <p key={cat} style={{ fontSize: '12px', margin: '2px 0', color: counts[cat] > 0 ? '#333' : '#aaa' }}>
                          {cat}: {counts[cat]}
                        </p>
                      ))}
                      {CATEGORIES.every((c) => counts[c] === 0) && (
                        <p style={{ fontSize: '12px', color: '#aaa', fontStyle: 'italic' }}>No issues reported nearby</p>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}

            {endId && locations.filter((l) => l.id === endId).map((loc) => {
              const counts = getCategoryCounts(issues, loc.lat, loc.lng);
              return (
                <Marker key={loc.id} position={[loc.lat, loc.lng]} icon={createEndPin()}>
                  <Popup>
                    <div style={{ minWidth: '180px' }}>
                      <p style={{ fontWeight: 700, fontSize: '14px', marginBottom: '6px', color: '#b91c1c' }}>🔴 {loc.name} (End)</p>
                      <p style={{ fontSize: '11px', color: '#888', marginBottom: '6px' }}>Issues near here:</p>
                      {CATEGORIES.map((cat) => (
                        <p key={cat} style={{ fontSize: '12px', margin: '2px 0', color: counts[cat] > 0 ? '#333' : '#aaa' }}>
                          {cat}: {counts[cat]}
                        </p>
                      ))}
                      {CATEGORIES.every((c) => counts[c] === 0) && (
                        <p style={{ fontSize: '12px', color: '#aaa', fontStyle: 'italic' }}>No issues reported nearby</p>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
