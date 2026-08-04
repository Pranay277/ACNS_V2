import axios from "axios";
import { auth } from "./firebase";
import { clearSession, isAuthenticated, notifyReauthRequired } from "./session";

// Base URL is environment-driven. Create a frontend/.env file (see
// frontend/.env.example) to point the app at a deployed backend, e.g.
//   VITE_API_URL=https://api.example.com/api
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api"
});

// Every request is authenticated with the signed-in Firebase user's ID token
// (the backend verifies it and derives the caller's role/identity server-side).
// Login/signup are the only public endpoints; the backend ignores this header
// there and expects the token in the request body instead.
API.interceptors.request.use(async (config) => {
  try {
    const token = await auth.currentUser?.getIdToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (err) {
    console.warn("Could not attach auth token:", err);
  }
  return config;
});

// Response interceptor (P2-03):
//  * 403 + code REAUTH_REQUIRED → the token is valid but the auth_time claim is
//    older than FRESH_AUTH_MAX_AGE_SECONDS. Tag the error and notify the
//    ReauthModal so the user can re-enter their password (do NOT log out).
//  * Any other 401 while a session exists → the ID token is invalid, expired,
//    or revoked (e.g. admin deactivated the account or reset its password
//    server-side). Clear the session so route guards force a clean re-login.
API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const code = error.response?.data?.code;
    if (status === 403 && code === "REAUTH_REQUIRED") {
      error.reauthRequired = true;
      notifyReauthRequired();
    } else if (status === 401 && isAuthenticated()) {
      clearSession();
    }
    return Promise.reject(error);
  }
);

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
