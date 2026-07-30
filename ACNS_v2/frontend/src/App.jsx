import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import PageTransition from "./components/PageTransition";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ReportIssue from "./pages/ReportIssue";
import DashboardUser from "./pages/DashboardUser";
import UserNavigate from "./pages/UserNavigate";
import Leaderboard from "./pages/Leaderboard";
import DashboardSupervisor from "./pages/DashboardSupervisor";
import DashboardAdmin from "./pages/DashboardAdmin";
import AdminIssues from "./pages/AdminIssues";

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <PageTransition key={location.pathname}>
      <Routes location={location}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/report" element={<ReportIssue />} />
        <Route path="/user" element={<DashboardUser />} />
        <Route path="/user/navigate" element={<UserNavigate />} />
        <Route path="/user/leaderboard" element={<Leaderboard />} />
        <Route path="/supervisor" element={<DashboardSupervisor />} />
        <Route path="/admin" element={<DashboardAdmin />} />
        <Route path="/admin/issues" element={<AdminIssues />} />
      </Routes>
    </PageTransition>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  );
}

export default App;