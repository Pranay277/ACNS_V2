import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import PageTransition from "./components/PageTransition";
import ReauthModal from "./components/ReauthModal";
import {
  ProtectedRoute,
  RequireStudent,
  RequireSupervisor,
  RequireAdmin,
} from "./components/guards";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ReportIssue from "./pages/ReportIssue";
import DashboardUser from "./pages/DashboardUser";
import UserNavigate from "./pages/UserNavigate";
import Leaderboard from "./pages/Leaderboard";
import DashboardSupervisor from "./pages/DashboardSupervisor";
import SupervisorProfile from "./pages/SupervisorProfile";
import DashboardAdmin from "./pages/DashboardAdmin";
import AdminIssues from "./pages/AdminIssues";
import SupervisorManagement from "./pages/SupervisorManagement";
import IssueDetails from "./pages/IssueDetails";

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <PageTransition key={location.pathname}>
      <Routes location={location}>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Student routes */}
        <Route
          path="/report"
          element={<RequireStudent><ReportIssue /></RequireStudent>}
        />
        <Route
          path="/user"
          element={<RequireStudent><DashboardUser /></RequireStudent>}
        />
        <Route
          path="/user/navigate"
          element={<RequireStudent><UserNavigate /></RequireStudent>}
        />
        <Route
          path="/user/leaderboard"
          element={<RequireStudent><Leaderboard /></RequireStudent>}
        />

        {/* Supervisor routes */}
        <Route
          path="/supervisor"
          element={<RequireSupervisor><DashboardSupervisor /></RequireSupervisor>}
        />
        <Route
          path="/supervisor/profile"
          element={<RequireSupervisor><SupervisorProfile /></RequireSupervisor>}
        />

        {/* Shared authenticated route (issue detail via SMS links) */}
        <Route
          path="/issues/:campusId/:issueId"
          element={<ProtectedRoute><IssueDetails /></ProtectedRoute>}
        />

        {/* Admin routes */}
        <Route
          path="/admin"
          element={<RequireAdmin><DashboardAdmin /></RequireAdmin>}
        />
        <Route
          path="/admin/issues"
          element={<RequireAdmin><AdminIssues /></RequireAdmin>}
        />
        <Route
          path="/admin/supervisors"
          element={<RequireAdmin><SupervisorManagement /></RequireAdmin>}
        />
      </Routes>
    </PageTransition>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
      <ReauthModal />
    </BrowserRouter>
  );
}

export default App;