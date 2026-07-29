import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import NavbarUser from "../components/NavbarUser";
import IssueCard from "../components/IssueCard";
import MapView from "../components/MapView";
import { getIssues, getNotifications } from "../services/api";

export default function DashboardUser() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedIssue, setSelectedIssue] = useState(null);

  const [issues, setIssues] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = { email: "user1@gmail.com" }; // Mock integration
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getIssues({ role: "user", userId: user.email });
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
        const res = await getNotifications(user.email);
        setNotifications(res.data || []);
      } catch (err) {
        console.error(err);
      }
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 10000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: "Total Reported", value: issues.length, icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2", color: "bg-blue-500" },
    { label: "In Progress", value: issues.filter(i => i.status === "In Progress").length, icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z", color: "bg-yellow-500" },
    { label: "Resolved", value: issues.filter(i => i.status === "Resolved").length, icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z", color: "bg-green-500" },
  ];

  const filters = [
    { id: "all", label: "Total Issues" },
    { id: "Open", label: "Open" },
    { id: "In Progress", label: "In Progress" },
    { id: "Resolved", label: "Resolved" },
  ];

  const filteredIssues = selectedFilter === "all" 
    ? issues 
    : issues.filter(issue => issue.status === selectedFilter);

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
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={stat.icon} />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200">
            <div className="flex flex-wrap gap-2 p-4">
              {filters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setSelectedFilter(filter.id)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    selectedFilter === filter.id
                      ? "bg-primary-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-200 pb-2">Issue List</h2>
              {loading ? (
                <div className="text-center py-12 text-gray-400">Loading issues...</div>
              ) : filteredIssues.length > 0 ? (
                <div className="grid grid-cols-1 gap-4 h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                  {filteredIssues.map((issue) => (
                    <IssueCard key={issue.id} issue={issue} onClick={() => setSelectedIssue(issue)} />
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
              <MapView className="h-[600px] border border-gray-200" issues={filteredIssues.filter((i) => i.location?.lat && i.location?.lng)} />
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
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                  selectedIssue.status === "Open" ? "bg-red-100 text-red-800 border-red-200" :
                  selectedIssue.status === "In Progress" ? "bg-yellow-100 text-yellow-800 border-yellow-200" :
                  selectedIssue.status === "Resolved" ? "bg-green-100 text-green-800 border-green-200" :
                  "bg-gray-100 text-gray-600 border-gray-200"
                }`}>{selectedIssue.status}</span>
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

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
