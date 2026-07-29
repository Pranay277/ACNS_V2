import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ReportIssue from "./pages/ReportIssue";
import DashboardUser from "./pages/DashboardUser";
import DashboardSupervisor from "./pages/DashboardSupervisor";
import DashboardAdmin from "./pages/DashboardAdmin";
import AdminIssues from "./pages/AdminIssues";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/report" element={<ReportIssue />} />
        <Route path="/user" element={<DashboardUser />} />
        <Route path="/supervisor" element={<DashboardSupervisor />} />
        <Route path="/admin" element={<DashboardAdmin />} />
        <Route path="/admin/issues" element={<AdminIssues />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;