import { useState, useEffect, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import NavbarUser from "../components/NavbarUser";
import IssueCard from "../components/IssueCard";
import MapView from "../components/MapView";
import { getIssues, getNotifications } from "../services/api";
import safeUrl from "../utils/safeUrl";
import { STATUS_BADGE_STYLES_WITHOUT_CLOSED, STATUS_PILL_STYLES, GRAY_STATUS_BADGE } from "../constants/statusStyles";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const useCountUp = (target, duration = 800) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (target === 0) { setCount(0); return; }
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return count;
};

const COLLEGE_CENTERS = {
  "OU College":       { center: [17.4126, 78.5247], zoom: 15 },
  "Methodist College":{ center: [17.39181094222161, 78.47856891694526], zoom: 17 },
};

export default function DashboardUser() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedCollege, setSelectedCollege] = useState("");
  const [hoveredIssueId, setHoveredIssueId] = useState(null);
  const [locationModal, setLocationModal] = useState(null);
  const [mapCenter, setMapCenter] = useState(null);
  const [mapZoom, setMapZoom] = useState(null);

  const [issues, setIssues] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const user = useMemo(() => {
    try {
      const session = JSON.parse(localStorage.getItem("session_user") || "{}");
      if (session.email) {
        return {
          email: session.email,
          name: session.name || session.displayName || session.email,
          uid: session.uid,
          campusId: session.campusId,
        };
      }
    } catch {}
    return { email: "user1@gmail.com", name: "Student User" };
  }, []);

  const categories = [
    { id: "Infrastructure", label: "Infrastructure" },
    { id: "Electrical", label: "Electrical" },
    { id: "Cleanliness", label: "Cleanliness" },
    { id: "Safety", label: "Safety" },
    { id: "Transport", label: "Transport" },
    { id: "Environment", label: "Environment" },
  ];

  const colleges = [
    { id: "Methodist College", label: "Methodist College" },
    { id: "OU College", label: "OU College" },
  ];
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getIssues({ role: "user", userId: user.uid || user.email });
        setIssues(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [location.key]);

  useEffect(() => {
    const fetchNotifs = async () => {
      try {
        const res = await getNotifications(user.uid || user.email);
        setNotifications(res.data || []);
      } catch (err) {
        console.error(err);
      }
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedCollege) { setMapCenter(null); setMapZoom(null); return; }
    const entry = COLLEGE_CENTERS[selectedCollege];
    if (entry) { setMapCenter(entry.center); setMapZoom(entry.zoom); }
  }, [selectedCollege]);

  const filters = [
    { id: "all", label: "Total Issues" },
    { id: "Open", label: "Open" },
    { id: "In Progress", label: "In Progress" },
    { id: "Resolved", label: "Resolved" },
  ];

  const filteredIssues = issues.filter(issue => {
    const statusMatch = selectedFilter === "all" || issue.status === selectedFilter;
    const categoryMatch = !selectedCategory || issue.category === selectedCategory;
    const collegeMatch = !selectedCollege || 
      (issue.college && issue.college === selectedCollege) ||
      (issue.location?.text && issue.location.text.toLowerCase().includes(selectedCollege.toLowerCase()));
    return statusMatch && categoryMatch && collegeMatch;
  });

  const categoryData = useMemo(() => {
    const counts = issues.reduce((acc, issue) => {
      const cat = issue.category || 'Other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [issues]);

  const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

  const recentActivity = useMemo(() => {
    return [...issues]
      .sort((a, b) => new Date(b.updatedAt || b.createdAt) - new Date(a.updatedAt || a.createdAt))
      .slice(0, 5);
  }, [issues]);

  const animatedTotal = useCountUp(issues.length);
  const animatedInProgress = useCountUp(issues.filter(i => i.status === "In Progress").length);
  const animatedResolved = useCountUp(issues.filter(i => i.status === "Resolved").length);

  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarUser />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Dashboard</h1>
            <p className="mt-1 text-gray-500">Track and manage your reported civic issues</p>
          </div>
          <button
            onClick={() => navigate("/report")}
            className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Report New Issue
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
            <div className="flex items-center">
              <div className="bg-blue-500 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Reported</p>
                <p className="text-2xl font-bold text-gray-900 tabular-nums">{animatedTotal}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
            <div className="flex items-center">
              <div className="bg-yellow-500 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">In Progress</p>
                <p className="text-2xl font-bold text-gray-900 tabular-nums">{animatedInProgress}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
            <div className="flex items-center">
              <div className="bg-green-500 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Resolved</p>
                <p className="text-2xl font-bold text-gray-900 tabular-nums">{animatedResolved}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 p-4">
            <div className="flex flex-wrap gap-2 mb-3">
              {filters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setSelectedFilter(filter.id)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    selectedFilter === filter.id
                      ? "bg-primary-600 text-white shadow-md"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 items-center bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</span>
              </div>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white min-w-[140px]"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.label}</option>
                ))}
              </select>
              <div className="h-4 w-px bg-gray-300"></div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Location</span>
              </div>
              <select
                value={selectedCollege}
                onChange={(e) => setSelectedCollege(e.target.value)}
                className="px-3 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white min-w-[160px]"
              >
                <option value="">All Locations</option>
                {colleges.map((college) => (
                  <option key={college.id} value={college.id}>{college.label}</option>
                ))}
              </select>
              {(selectedCategory || selectedCollege) && (
                <button
                  onClick={() => { setSelectedCategory(""); setSelectedCollege(""); }}
                  className="ml-auto px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors flex items-center gap-1"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Clear
                </button>
              )}
            </div>
            {(selectedCategory || selectedCollege) && (
              <p className="mt-2 text-xs text-gray-500">
                Showing {filteredIssues.length} of {issues.length} issues
              </p>
            )}
          </div>

          <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-200 pb-2">Issue List</h2>
              {loading ? (
                <div className="text-center py-12 text-gray-400">Loading issues...</div>
              ) : filteredIssues.length > 0 ? (
                <div className="grid grid-cols-1 gap-4 h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                  {filteredIssues.map((issue) => (
                    <IssueCard
                      key={issue.id}
                      issue={issue}
                      onClick={() => setSelectedIssue(issue)}
                      onMouseEnter={() => setHoveredIssueId(issue.id || issue._id)}
                      onMouseLeave={() => setHoveredIssueId(null)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No issues found</h3>
                  <p className="mt-1 text-sm text-gray-500">No issues match your current filter.</p>
                </div>
              )}
            </div>

            <div className="flex flex-col sticky top-6 self-start">
              <h2 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-200 pb-2">Issue Map</h2>
              <MapView className="h-[600px] border border-gray-200" issues={filteredIssues.filter((i) => i.location?.lat && i.location?.lng)} hoveredIssueId={hoveredIssueId} center={mapCenter} zoom={mapZoom} />
            </div>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Issues by Category
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory("")}
                  className="ml-auto text-xs text-primary-600 hover:text-primary-800 bg-primary-50 px-2 py-1 rounded-md"
                >
                  Clear filter
                </button>
              )}
            </h3>
            {!selectedCategory && (
              <p className="text-xs text-gray-400 mb-3 -mt-2">Click a slice to filter issues by category</p>
            )}
            {categoryData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={selectedCategory ? 85 : 80}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                          stroke={selectedCategory === entry.name ? '#1e40af' : 'none'}
                          strokeWidth={selectedCategory === entry.name ? 3 : 0}
                          style={{ cursor: 'pointer', opacity: selectedCategory && selectedCategory !== entry.name ? 0.5 : 1 }}
                          onClick={() => setSelectedCategory(entry.name === selectedCategory ? '' : entry.name)}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">No data available</div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Recent Activity
            </h3>
            {recentActivity.length > 0 ? (
              <div className="space-y-3 h-64 overflow-y-auto">
                {recentActivity.map((issue) => (
                  <div key={issue.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{issue.description || 'No description'}</p>
                      <p className="text-xs text-gray-500">{new Date(issue.updatedAt || issue.createdAt).toLocaleDateString()}</p>
                    </div>
                    <span className={`ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_PILL_STYLES[issue.status] || STATUS_PILL_STYLES.Closed}`}>{issue.status}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">No recent activity</div>
            )}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg. Resolution</p>
                <p className="text-xl font-bold text-gray-900">
                  {issues.filter(i => i.status === 'Resolved').length > 0 ? '2-3 days' : 'N/A'}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">Top Category</p>
                <p className="text-xl font-bold text-gray-900">{categoryData[0]?.name || 'N/A'}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-500">Locations Reported</p>
                <p className="text-xl font-bold text-gray-900">{new Set(issues.map(i => i.location?.text).filter(Boolean)).size}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-gradient-to-r from-primary-600 to-indigo-600 rounded-xl shadow-lg p-6 text-white">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold mb-1">Want to make a difference?</h3>
              <p className="text-primary-100">Report an issue in your community and help improve your neighborhood.</p>
            </div>
            <button
              onClick={() => navigate("/report")}
              className="mt-4 md:mt-0 bg-white text-primary-600 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Report an Issue
            </button>
          </div>
        </div>
      </div>

      {/* Issue Detail Popup */}
      {selectedIssue && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
          onClick={() => setSelectedIssue(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-gray-900">Issue Report</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUS_BADGE_STYLES_WITHOUT_CLOSED[selectedIssue.status] || GRAY_STATUS_BADGE}`}>{selectedIssue.status}</span>
              </div>
              <button
                onClick={() => setSelectedIssue(null)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body — only user-provided fields */}
            <div className="px-6 py-5 space-y-4">

              {/* Category */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Category</p>
                <p className="text-sm font-medium text-gray-800">{selectedIssue.category || "—"}</p>
              </div>

              {/* Description */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Description</p>
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{selectedIssue.description || "—"}</p>
              </div>

              {/* Location text */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Location</p>
                <p className="text-sm text-gray-700">{selectedIssue.location?.text || "Not specified"}</p>
              </div>

              {/* Coordinates */}
              {selectedIssue.location?.lat && selectedIssue.location?.lng && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Coordinates</p>
                  <button
                    onClick={() => setLocationModal(selectedIssue.location)}
                    className="text-sm text-primary-600 hover:text-primary-800 font-mono flex items-center gap-1"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {selectedIssue.location.lat.toFixed(5)}, {selectedIssue.location.lng.toFixed(5)}
                  </button>
                </div>
              )}

              {/* College */}
              {selectedIssue.college && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">College</p>
                  <p className="text-sm text-gray-700">{selectedIssue.college}</p>
                </div>
              )}

              {/* Reported Date & Time */}
              {selectedIssue.createdAt && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Reported On</p>
                  <p className="text-sm text-gray-700">
                    {new Date(selectedIssue.createdAt).toLocaleDateString('en-IN', { 
                      day: '2-digit', month: 'long', year: 'numeric' 
                    })} at {new Date(selectedIssue.createdAt).toLocaleTimeString('en-IN', { 
                      hour: '2-digit', minute: '2-digit' 
                    })}
                  </p>
                </div>
              )}

              {/* Image */}
              {safeUrl(selectedIssue.imageUrl) && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Photo</p>
                  <img 
                    src={safeUrl(selectedIssue.imageUrl)} 
                    alt="Issue" 
                    className="w-full h-40 object-cover rounded-lg border border-gray-200 cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setLocationModal({ imageUrl: safeUrl(selectedIssue.imageUrl) })}
                  />
                </div>
              )}

            </div>
          </div>
        </div>
      )}

      {/* Location Map Modal */}
      {locationModal && locationModal.lat && locationModal.lng && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
          onClick={() => setLocationModal(null)}
        >
          <div className="relative max-w-3xl max-h-[90vh] w-full bg-white rounded-xl overflow-hidden">
            <button
              onClick={() => setLocationModal(null)}
              className="absolute top-3 right-3 z-10 p-2 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="p-2">
              <MapView 
                issues={[ { 
                  id: 'selected', 
                  location: { lat: locationModal.lat, lng: locationModal.lng, text: locationModal.text },
                  status: selectedIssue.status
                }]} 
                center={[locationModal.lat, locationModal.lng]}
                zoom={17}
                className="h-[60vh]"
              />
            </div>
            {locationModal.text && (
              <div className="p-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">{locationModal.text}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Image Modal */}
      {locationModal && locationModal.imageUrl && !locationModal.lat && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
          onClick={() => setLocationModal(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh] w-full">
            <button
              onClick={() => setLocationModal(null)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300 transition-colors"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <img 
              src={safeUrl(locationModal.imageUrl)} 
              alt="Issue" 
              className="max-w-full max-h-[85vh] mx-auto rounded-lg shadow-2xl"
            />
          </div>
        </div>
      )}
    </div>
  );
}
