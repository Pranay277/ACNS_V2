import axios from "axios";

// Base URL is environment-driven. Create a frontend/.env file (see
// frontend/.env.example) to point the app at a deployed backend, e.g.
//   VITE_API_URL=https://api.example.com/api
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api"
});

// AUTH & USERS
export const login = (idToken) => API.post("/auth/login", { idToken });
export const signup = (data) => API.post("/auth/signup", data);

// SUPERVISORS (admin-managed; all ops keyed by Firebase UID)
export const getSupervisors = (params) => API.get("/supervisors", { params });
export const createSupervisor = (data) => API.post("/supervisors", data);
export const getSupervisor = (uid) =>
  API.get(`/supervisors/${encodeURIComponent(uid)}`);
export const updateSupervisor = (uid, data) =>
  API.patch(`/supervisors/${encodeURIComponent(uid)}`, data);
export const updateMyProfile = (uid, data) =>
  API.patch(`/supervisors/${encodeURIComponent(uid)}/profile`, data);
export const changeSupervisorEmail = (uid, data) =>
  API.post(`/supervisors/${encodeURIComponent(uid)}/change-email`, data);
export const deactivateSupervisor = (uid) =>
  API.post(`/supervisors/${encodeURIComponent(uid)}/deactivate`);
export const activateSupervisor = (uid) =>
  API.post(`/supervisors/${encodeURIComponent(uid)}/activate`);
export const deleteSupervisor = (uid) =>
  API.delete(`/supervisors/${encodeURIComponent(uid)}`);
export const resetSupervisorPassword = (uid, data) =>
  API.post(`/supervisors/${encodeURIComponent(uid)}/reset-password`, data);

// CREATE ISSUE
export const createIssue = (data) => API.post("/issues", data);

// GET ISSUES
export const getIssues = (params) => API.get("/issues", { params });

// GET SINGLE ISSUE (Issue Details page)
export const getIssue = (id) => API.get(`/issues/${id}`);

// UPDATE STATUS
export const updateStatus = (id, data) => API.put(`/issues/${id}/status`, data);

// VERIFY
export const verifyIssue = (id, data) => API.post(`/issues/${id}/verify`, data);

// NOTIFICATIONS
export const getNotifications = (userId) =>
  API.get(`/notifications/${userId}`);

// GAMIFICATION
export const getLeaderboard = (params) =>
  API.get("/gamification/leaderboard", { params });
export const getUserGamification = (userId) =>
  API.get(`/gamification/user/${userId}`);
export default API;
