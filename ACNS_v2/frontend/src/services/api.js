import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/api"
});

// CREATE ISSUE
export const createIssue = (data) => API.post("/issues", data);

// GET ISSUES
export const getIssues = (params) => API.get("/issues", { params });

// UPDATE STATUS
export const updateStatus = (id, data) => API.put(`/issues/${id}/status`, data);

// VERIFY
export const verifyIssue = (id, data) => API.post(`/issues/${id}/verify`, data);

// NOTIFICATIONS
export const getNotifications = (userId) =>
  API.get(`/notifications/${userId}`);

export default API;
