import { useEffect, useState } from "react";
import { EmailAuthProvider, reauthenticateWithCredential } from "firebase/auth";
import { auth, mapFirebaseAuthError } from "../services/firebase";
import { subscribeReauthRequired } from "../services/session";

// Global re-authentication prompt (P2-03).
//
// The backend guards sensitive account-lifecycle actions (deactivate /
// activate / change-email / reset-password / delete) with a fresh-auth check:
// a 403 REAUTH_REQUIRED is returned when the Firebase `auth_time` claim is
// older than FRESH_AUTH_MAX_AGE_SECONDS. `api.js` notifies this component,
// which asks the user for their password. A successful
// reauthenticateWithCredential performs a fresh sign-in, so the next
// getIdToken(true) carries an up-to-date auth_time and the pending action can
// be retried.
export default function ReauthModal() {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => subscribeReauthRequired(() => setOpen(true)), []);

  const close = () => {
    setOpen(false);
    setPassword("");
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const user = auth.currentUser;
    if (!user) return close();
    if (!password) return setError("Enter your password to confirm your identity.");

    setSubmitting(true);
    try {
      const credential = EmailAuthProvider.credential(user.email, password);
      await reauthenticateWithCredential(user, credential);
      // Force a fresh ID token so the updated auth_time is carried on the
      // next request and passes require_recent_auth.
      await user.getIdToken(true);
      close();
    } catch (err) {
      setError(mapFirebaseAuthError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60">
      <div
        className="relative w-full max-w-md bg-white rounded-xl shadow-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-bold text-gray-900">Confirm your identity</h3>
          <button onClick={close} className="text-gray-400 hover:text-gray-600 transition-colors" aria-label="Close">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          For your security, this action requires a recent sign-in. Please
          re-enter your password to continue.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reauth-password" className="block text-sm font-medium text-gray-700 mb-1.5">
              Password
            </label>
            <input
              id="reauth-password"
              type="password"
              autoFocus
              placeholder="Enter your password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (error) setError("");
              }}
              className="w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={close} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Confirming..." : "Confirm"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
