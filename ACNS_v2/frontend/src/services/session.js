// Session helpers — single source of truth for the client-side session.
//
// Sessions are plain localStorage objects keyed per-role (session_user,
// session_supervisor, session_admin) written on login. These guards are
// defense-in-depth + UX only: the backend is the real authorization boundary
// and always verifies the Firebase ID token + role server-side.
import { auth } from "./firebase";

const SESSION_PREFIX = "session_";

// role -> landing page used for post-login redirects and wrong-role redirects.
export const ROLE_HOME = {
  user: "/user",
  supervisor: "/supervisor",
  admin: "/admin",
};

function parseSession(role) {
  try {
    const raw = localStorage.getItem(SESSION_PREFIX + role);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || data.role !== role || !data.email) return null;
    return { role, ...data };
  } catch {
    return null;
  }
}

export function getSession(role) {
  return parseSession(role);
}

// Resolve the active session. Prefers the session whose uid matches the
// current Firebase user (handles stale sessions from earlier logins), then
// falls back to whichever role session exists.
export function getCurrentSession() {
  const uid = auth.currentUser?.uid;
  const roles = Object.keys(ROLE_HOME);

  if (uid) {
    for (const role of roles) {
      const session = parseSession(role);
      if (session && session.uid === uid) return session;
    }
  }

  for (const role of roles) {
    const session = parseSession(role);
    if (session) return session;
  }

  return null;
}

export function isAuthenticated() {
  return getCurrentSession() !== null;
}

export function hasRole(role) {
  return getCurrentSession()?.role === role;
}

// Clears every role session. Used on logout so stale sessions from a previous
// login can never satisfy a route guard.
export function clearSession() {
  Object.keys(ROLE_HOME).forEach((role) =>
    localStorage.removeItem(SESSION_PREFIX + role)
  );
}

// Full logout: end the Firebase Auth session (so the ID token can no longer be
// minted) AND wipe every localStorage session. P2-03 — previously we only
// cleared localStorage, leaving a live Firebase session behind.
export async function logout() {
  try {
    if (auth.currentUser) await auth.signOut();
  } finally {
    clearSession();
  }
}

// ── Re-authentication requests (P2-03) ──────────────────────────────────────
// The backend guards sensitive admin actions with require_recent_auth (a 403
// with code REAUTH_REQUIRED when the Firebase auth_time is too old). The
// API layer notifies these listeners so a global ReauthModal can prompt the
// user to re-enter their password. This is a minimal pub/sub, not React state.
let reauthListeners = new Set();

export function subscribeReauthRequired(listener) {
  reauthListeners.add(listener);
  return () => reauthListeners.delete(listener);
}

export function notifyReauthRequired() {
  reauthListeners.forEach((listener) => {
    try {
      listener();
    } catch {
      // A broken listener must never break the request pipeline.
    }
  });
}
