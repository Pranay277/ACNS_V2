// Reusable route guards.
//
// Purpose: UX + defense-in-depth. The backend enforces every authorization
// decision; these guards only keep unauthorized users out of screens and
// redirect them somewhere useful.
//
//   ProtectedRoute     — any authenticated user (any role).
//   RequireRole        — authenticated AND one of the listed roles.
//   RequireStudent     — role "user"  only.
//   RequireSupervisor  — role "supervisor" only.
//   RequireAdmin       — role "admin" only.
import { Navigate } from "react-router-dom";
import { getCurrentSession, ROLE_HOME } from "../services/session";

function LandingFor(role) {
  return ROLE_HOME[role] || "/login";
}

function Redirect({ session }) {
  return <Navigate to={session ? LandingFor(session.role) : "/login"} replace />;
}

export function ProtectedRoute({ children }) {
  const session = getCurrentSession();
  if (!session) return <Navigate to="/login" replace />;
  return children;
}

export function RequireRole({ roles = [], children }) {
  const session = getCurrentSession();
  if (!session) return <Navigate to="/login" replace />;
  if (!roles.includes(session.role)) return <Redirect session={session} />;
  return children;
}

export function RequireStudent({ children }) {
  return <RequireRole roles={["user"]}>{children}</RequireRole>;
}

export function RequireSupervisor({ children }) {
  return <RequireRole roles={["supervisor"]}>{children}</RequireRole>;
}

export function RequireAdmin({ children }) {
  return <RequireRole roles={["admin"]}>{children}</RequireRole>;
}
