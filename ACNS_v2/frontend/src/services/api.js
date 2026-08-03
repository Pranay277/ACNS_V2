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
export const getUserProfile = (userId) => API.get(`/auth/profile/${userId}`);
export const getUsers = (params) => API.get("/auth/users", { params });
export const updateUser = (userId, data) => API.patch(`/auth/users/${userId}`, data);

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
