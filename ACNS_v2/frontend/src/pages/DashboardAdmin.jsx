import React, { useEffect, useState } from 'react';
import { getIssues, verifyIssue } from '../services/api';
import MapView from '../components/MapView';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import NavbarAdmin from '../components/NavbarAdmin';


const DashboardAdmin = () => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadIssues = async () => {
      try {
        const res = await getIssues({ role: "admin" });
        setIssues(Array.isArray(res.data) ? res.data : []);
      } catch {
        setIssues([]);
      } finally {
        setLoading(false);
      }
    };
    loadIssues();
  }, []);

  const handleVerify = async (id) => {
    try {
      await verifyIssue(id, { verified: true });
      alert("Issue marked as verified successfully.");
    } catch (err) {
      console.error(err);
      alert("Failed to verify issue.");
    }
  };

  const getUserStats = () => {
    const userCount = {};
    const areaCount = {};
    
    issues.forEach(issue => {
      if (issue.userId) {
        userCount[issue.userId] = (userCount[issue.userId] || 0) + 1;
      }
      if (issue.location?.text) {
        areaCount[issue.location.text] = (areaCount[issue.location.text] || 0) + 1;
      }
    });

    const topUsers = Object.entries(userCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));

    const areaBreakdown = Object.entries(areaCount)
      .sort((a, b) => b[1] - a[1])
      .map(([area, count]) => ({ area, count }));

    return { totalUsers: Object.keys(userCount).length, topUsers, areaBreakdown };
  };

  const userStats = getUserStats();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="w-12 h-12 border-b-2 border-blue-500 rounded-full animate-spin mb-4" />
        <p className="text-gray-400">Loading dashboard data…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <NavbarAdmin />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12"><MapView issues={issues} /></div>
          <div className="col-span-12"><AnalyticsDashboard issues={issues} /></div>
          
          <div className="col-span-12 lg:col-span-6 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">User Statistics</h3>
            <div className="mb-4">
              <p className="text-3xl font-bold text-indigo-600">{userStats.totalUsers}</p>
              <p className="text-sm text-gray-500">Total Users</p>
            </div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Top Complainants</h4>
            {userStats.topUsers.length > 0 ? (
              <ul className="space-y-2">
                {userStats.topUsers.map((user, idx) => (
                  <li key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700 truncate">{user.name}</span>
                    <span className="text-sm font-semibold text-indigo-600">{user.count}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No data available</p>
            )}
          </div>

          <div className="col-span-12 lg:col-span-6 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Area Breakdown</h3>
            {userStats.areaBreakdown.length > 0 ? (
              <ul className="space-y-3">
                {userStats.areaBreakdown.map((item, idx) => (
                  <li key={idx}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-700">{item.area}</span>
                      <span className="text-sm font-semibold text-indigo-600">{item.count}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full"
                        style={{ width: `${(item.count / issues.length) * 100}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No data available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardAdmin;
