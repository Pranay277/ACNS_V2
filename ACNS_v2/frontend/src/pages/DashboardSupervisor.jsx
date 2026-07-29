import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import SupervisorTaskList from "../components/SupervisorTaskList";
import DashboardCharts from "../components/DashboardCharts";
import { getIssues } from "../services/api";

const DashboardSupervisor = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  
  const savedUser = JSON.parse(localStorage.getItem("session_supervisor") || "{}");
  const user = savedUser.email ? savedUser : { email: "supervisor1@gmail.com" };

  const fetchTasks = async () => {
    try {
      const res = await getIssues({ role: "supervisor", email: user.email });
      const tasksArray = Array.isArray(res.data) ? res.data : [];
      const sortedTasks = tasksArray.sort((a, b) => (b.reportCount || 1) - (a.reportCount || 1));
      setTasks(sortedTasks);
    } catch (err) {
      console.error("Failed to fetch tasks in polling:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const stats = {
    open: tasks.filter((t) => t.status === "Open").length,
    inProgress: tasks.filter((t) => t.status === "In Progress").length,
    resolved: tasks.filter((t) => t.status === "Resolved" || t.status === "Closed").length,
    total: tasks.length,
  };

  const searchParams = new URLSearchParams(location.search);
  const isResolvedView = searchParams.get("filter") === "resolved";
  const displayedTasks = isResolvedView 
    ? tasks.filter(t => t.status === "Resolved" || t.status === "Closed")
    : tasks;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Supervisor Dashboard</h1>
          <p className="mt-1 text-gray-500">Manage assigned tasks and track issue resolution</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className={isResolvedView ? "lg:col-span-3" : "lg:col-span-2"}>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">{isResolvedView ? "Resolved Issues" : "My Tasks"}</h2>
              <SupervisorTaskList tasks={displayedTasks} loading={loading} onStatusChange={fetchTasks} />
            </div>
          </div>

          {!isResolvedView && (
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-24">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Stats</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-100 transition-colors duration-300">
                  <div>
                    <p className="text-sm text-red-600 font-medium">Open</p>
                    <p className="text-2xl font-bold text-red-700">{stats.open}</p>
                  </div>
                  <div className="p-3 bg-red-100 rounded-full">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-100 transition-colors duration-300">
                  <div>
                    <p className="text-sm text-yellow-600 font-medium">In Progress</p>
                    <p className="text-2xl font-bold text-yellow-700">{stats.inProgress}</p>
                  </div>
                  <div className="p-3 bg-yellow-100 rounded-full">
                    <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-100 transition-colors duration-300">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Resolved</p>
                    <p className="text-2xl font-bold text-green-700">{stats.resolved}</p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-full">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-100 transition-colors duration-300">
                  <div>
                    <p className="text-sm text-blue-600 font-medium">Total</p>
                    <p className="text-2xl font-bold text-blue-700">{stats.total}</p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-full">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
          )}
        </div>

        {!isResolvedView && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Analytics</h2>
          <DashboardCharts tasks={tasks} />
        </div>
        )}
      </div>
    </div>
  );
};

export default DashboardSupervisor;

