import { signOut } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { auth, db } from "./firebase";

export function saveSession(role, firebaseUser, token) {
  const session = {
    uid: firebaseUser.uid,
    email: firebaseUser.email,
    role,
    name: firebaseUser.displayName || "",
    token,
  };
  localStorage.setItem(`session_${role}`, JSON.stringify(session));
}

export async function saveUserProfile(firebaseUser, { name, role = "Student" } = {}) {
  const userRef = doc(db, "users", firebaseUser.uid);
  await setDoc(
    userRef,
    {
      name: name || firebaseUser.displayName || firebaseUser.email || "",
      email: firebaseUser.email || "",
      role,
      createdAt: serverTimestamp(),
    },
    { merge: true }
  );
}

export function getSession(role) {
  try {
    const raw = localStorage.getItem(`session_${role}`);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearSession(role) {
  if (role) localStorage.removeItem(`session_${role}`);
}

export function clearAllSessions() {
  localStorage.removeItem("session_user");
  localStorage.removeItem("session_supervisor");
  localStorage.removeItem("session_admin");
}

export async function signOutUser() {
  clearAllSessions();
  try {
    await signOut(auth);
  } catch {
    // already signed out
  }
}

export function getAuthErrorMessage(error) {
  const code = error?.code || "";
  const messages = {
    "auth/email-already-in-use":
      "An account with this email already exists. Please sign in instead.",
    "auth/invalid-email": "Please enter a valid email address.",
    "auth/weak-password": "Password is too weak. Use at least 6 characters.",
    "auth/user-not-found": "Invalid email or password.",
    "auth/wrong-password": "Invalid email or password.",
    "auth/invalid-credential": "Invalid email or password.",
    "auth/too-many-requests": "Too many sign-in attempts. Please try again later.",
    "auth/operation-not-allowed":
      "Email/password sign-in is not enabled in your Firebase project.",
    "auth/network-request-failed": "Network error. Please check your connection.",
    "auth/invalid-api-key":
      "Firebase configuration is missing or invalid. Set your VITE_FIREBASE_* variables in a .env file.",
    "auth/unauthorized-domain":
      "This domain is not authorized for Firebase Authentication. Add it in the Firebase console.",
  };
  return messages[code] || error?.message || "Something went wrong. Please try again.";
}
