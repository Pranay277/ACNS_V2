// Client-side mirror of the backend password policy (P2-08) so users get
// immediate feedback before a request is even sent. The backend enforces the
// same rules authoritatively (see shared/utils/validators.py validate_password).
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`";

// Returns an error string when the password fails the policy, otherwise null.
export function validatePassword(password) {
  const value = String(password || "");
  const missing = [];
  if (value.length < PASSWORD_MIN_LENGTH) missing.push(`at least ${PASSWORD_MIN_LENGTH} characters`);
  if (!/[A-Z]/.test(value)) missing.push("an uppercase letter");
  if (!/[a-z]/.test(value)) missing.push("a lowercase letter");
  if (!/\d/.test(value)) missing.push("a digit");
  if (!new RegExp(`[${PASSWORD_SPECIAL_CHARS.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}]`).test(value)) {
    missing.push("a special character");
  }
  if (missing.length) return "Password must include " + missing.join(", ") + ".";
  return null;
}
