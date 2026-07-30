import { useState, useEffect } from "react";
import NavbarUser from "../components/NavbarUser";
import { getIssues } from "../services/api";

const POINTS = { Resolved: 10, "In Progress": 5, Open: 2 };

function isThisMonth(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
}

function computeMonthlyLeaderboard(issues) {
  const userMap = {};
  issues.forEach((issue) => {
    const email = issue.userId || issue.email || "unknown@campus.edu";
    if (!userMap[email]) userMap[email] = { email, issues: 0, points: 0 };
    userMap[email].issues++;
    userMap[email].points += POINTS[issue.status] || 2;
  });
  return Object.values(userMap).sort((a, b) => b.points - a.points || b.issues - a.issues);
}

const medals = ["text-yellow-500", "text-gray-400", "text-amber-700"];

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [myOverall, setMyOverall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    try {
      const s = localStorage.getItem("session_user");
      if (s) setUserEmail(JSON.parse(s).email || "");
    } catch {}
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const res = await getIssues({});
        const all = Array.isArray(res.data) ? res.data : [];
        const monthly = all.filter((i) => isThisMonth(i.createdAt || i.date || i.timestamp));
        const pool = monthly.length >= 3 ? monthly : all;
        const lb = computeMonthlyLeaderboard(pool);

        const overallSorted = computeMonthlyLeaderboard(all);
        const idx = overallSorted.findIndex((u) => u.email === userEmail);
        setMyOverall(idx === -1 ? null : { rank: idx + 1, user: overallSorted[idx] });
        setLeaderboard(lb);
      } catch {
        setLeaderboard([]);
        setMyOverall(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [userEmail]);

  const top5 = leaderboard.slice(0, 5);
  const myTop5Index = top5.findIndex((u) => u.email === userEmail);
  const monthName = new Date().toLocaleString("default", { month: "long", year: "numeric" });

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <NavbarUser />

      <div className="max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Leaderboard</h1>
            <p className="mt-1 text-gray-500">Who&apos;s making a difference this month</p>
          </div>
          {myOverall && (
            <div className="flex items-center gap-3 px-4 py-2 bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Your rank</span>
                <span className="text-xl font-bold text-primary-600">#{myOverall.rank}</span>
              </div>
              <div className="w-px h-6 bg-gray-200" />
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Points</span>
                <span className="text-xl font-bold text-primary-600">{myOverall.user?.points ?? 0}</span>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <svg className="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
                <span className="text-xl">🔥</span>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Monthly Champions</h2>
                  <p className="text-xs text-gray-400">{monthName}</p>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {top5.length === 0 ? (
                  <div className="px-6 py-12 text-center">
                    <p className="text-gray-400">No reports yet this month</p>
                    <p className="text-sm text-gray-300 mt-1">Be the first to make a difference!</p>
                  </div>
                ) : (
                  top5.map((u, i) => {
                    const isMe = u.email === userEmail;
                    return (
                      <div
                        key={u.email}
                        className={`flex items-center gap-4 px-6 py-4 ${isMe ? "bg-primary-50" : "hover:bg-gray-50"} transition-colors`}
                      >
                        <div className="flex-shrink-0 w-10 text-center">
                          {i < 3 ? (
                            <svg className={`w-7 h-7 mx-auto ${medals[i]}`} fill="currentColor" viewBox="0 0 20 20">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ) : (
                            <span className="text-lg font-bold text-gray-400">#{i + 1}</span>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${isMe ? "text-primary-700" : "text-gray-900"}`}>
                            {u.email}
                            {isMe && <span className="ml-2 text-xs text-primary-500 font-semibold">(You)</span>}
                          </p>
                          <p className="text-xs text-gray-500">{u.issues} issue{u.issues !== 1 ? "s" : ""}</p>
                        </div>
                        <div className="flex-shrink-0 text-right">
                          <p className="text-lg font-bold text-gray-900">{u.points}</p>
                          <p className="text-xs text-gray-500">pts</p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {myTop5Index === -1 && myOverall && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-bold text-gray-400">#{myOverall.rank}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {myOverall.user.email}
                        <span className="ml-2 text-xs text-primary-500 font-semibold">(You)</span>
                      </p>
                      <p className="text-xs text-gray-500">{myOverall.user.issues} issue{myOverall.user.issues !== 1 ? "s" : ""}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">{myOverall.user.points}</p>
                    <p className="text-xs text-gray-500">pts</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
