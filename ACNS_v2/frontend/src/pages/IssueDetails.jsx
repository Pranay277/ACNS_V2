import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import MapView from "../components/MapView";
import CameraCapture from "../components/CameraCapture";
import { getIssue, updateStatus, verifyIssue } from "../services/api";
import { STATUS_BADGE_STYLES } from "../constants/statusStyles";

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const DetailRow = ({ label, value }) => (
  <div className="py-3 border-b border-gray-100 last:border-b-0">
    <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</dt>
    <dd className="mt-1 text-sm font-medium text-gray-800">{value || "—"}</dd>
  </div>
);

const IssueDetails = () => {
  const { campusId, issueId } = useParams();
  const [issue, setIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Mark Resolved modal state (reuses the SupervisorTaskList pattern)
  const [resolveOpen, setResolveOpen] = useState(false);
  const [proofImage, setProofImage] = useState(null);
  const [proofPreview, setProofPreview] = useState(null);
  const [resolveNote, setResolveNote] = useState("");
  const [imageError, setImageError] = useState("");
  const [showCamera, setShowCamera] = useState(false);

  const fetchIssue = async () => {
    try {
      const res = await getIssue(issueId);
      setIssue(res.data.issue);
      setNotFound(false);
      setError("");
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setNotFound(true);
      } else {
        setError("Failed to load issue. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssue();
  }, [issueId]);

  const refresh = async () => {
    const res = await getIssue(issueId);
    setIssue(res.data.issue);
  };

  const handleStartWork = async () => {
    setBusy(true);
    try {
      await updateStatus(issueId, { status: "In Progress" });
      await refresh();
    } catch (err) {
      console.error(err);
      alert("Failed to start work. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const openResolveModal = () => {
    setResolveOpen(true);
    setProofImage(null);
    setProofPreview(null);
    setResolveNote("");
    setImageError("");
  };

  const handleProofImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProofImage(file);
      setImageError("");
      const reader = new FileReader();
      reader.onloadend = () => setProofPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleResolveSubmit = async () => {
    if (!proofPreview) {
      setImageError("Proof image is required to mark as resolved.");
      return;
    }
    setBusy(true);
    try {
      await updateStatus(issueId, {
        status: "Resolved",
        proofImageUrl: proofPreview,
        supervisorDescription: resolveNote || undefined,
      });
      setResolveOpen(false);
      await refresh();
    } catch (err) {
      console.error(err);
      alert("Failed to mark as resolved. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleVerify = async (verified) => {
    setBusy(true);
    try {
      await verifyIssue(issueId, { verified });
      await refresh();
    } catch (err) {
      console.error(err);
      alert("Failed to update verification. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-gray-400">
        Loading issue...
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center text-center px-4">
        <p className="text-6xl mb-4">🔍</p>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Issue not found</h1>
        <p className="text-gray-500 mb-6">This issue may have been removed.</p>
        <Link to="/" className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg">
          Go Home
        </Link>
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center text-center px-4">
        <p className="text-gray-500 mb-4">{error || "Issue not found"}</p>
        <button
          onClick={() => { setLoading(true); fetchIssue(); }}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  const location = issue.location || {};
  const hasImage = Boolean(issue.imageUrl);
  const canStart = issue.status === "Open";
  const canResolve = issue.status === "In Progress";
  const canVerify = issue.status === "Resolved";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
            SCIARS
          </Link>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full text-xs font-medium border bg-gray-50 text-gray-600">
              {issue.category}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_BADGE_STYLES[issue.status] || STATUS_BADGE_STYLES.Open}`}>
              {issue.status}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Issue Details</h1>
            <p className="text-sm text-gray-500 mt-1">Reported {formatDate(issue.createdAt)}</p>
          </div>
          <Link to="/supervisor" className="text-sm font-medium text-primary-600 hover:text-primary-700">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column: image + description */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {hasImage ? (
                <a href={issue.imageUrl} target="_blank" rel="noreferrer" title="Open uploaded image">
                  <img
                    src={issue.imageUrl}
                    alt={issue.description || "Uploaded issue image"}
                    className="w-full max-h-80 object-cover"
                  />
                </a>
              ) : (
                <div className="h-48 bg-gray-100 flex flex-col items-center justify-center text-gray-400">
                  <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm">No uploaded image</span>
                </div>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Description</h2>
              <p className="text-gray-700 leading-relaxed">{issue.description || "—"}</p>
              {issue.proofImageUrl && issue.status !== "Open" && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Resolution Proof</h3>
                  <a href={issue.proofImageUrl} target="_blank" rel="noreferrer">
                    <img src={issue.proofImageUrl} alt="Resolution proof" className="max-h-48 rounded-lg" />
                  </a>
                </div>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Location</h2>
              {location.lat && location.lng ? (
                <MapView issues={[issue]} center={[location.lat, location.lng]} zoom={18} interactive={false} className="h-72" />
              ) : (
                <p className="text-sm text-gray-500">Location not specified.</p>
              )}
              {location.text && (
                <p className="mt-3 text-sm text-gray-600 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {location.text}
                </p>
              )}
            </div>
          </div>

          {/* Right column: details + supervisor actions */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Details</h2>
              <dl>
                <DetailRow label="Category" value={issue.category} />
                <DetailRow label="Campus" value={issue.campusName || issue.campusId || campusId} />
                <DetailRow label="Building" value={issue.buildingName || issue.buildingId} />
                <DetailRow label="Exact Location" value={location.text} />
                <DetailRow
                  label="Coordinates"
                  value={
                    location.lat != null && location.lng != null
                      ? `${Number(location.lat).toFixed(5)}, ${Number(location.lng).toFixed(5)}`
                      : "—"
                  }
                />
                <DetailRow label="Priority" value={issue.priority || "Normal"} />
                <DetailRow label="Status" value={issue.status} />
                <DetailRow label="Reported By" value={issue.userId} />
                <DetailRow label="Assigned To" value={issue.assignedTo} />
                <DetailRow label="Report Count" value={issue.reportCount || 1} />
                <DetailRow label="Date / Time" value={formatDate(issue.createdAt)} />
              </dl>
            </div>

            {(canStart || canResolve || canVerify) && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Supervisor Actions</h2>
                <div className="space-y-3">
                  {canStart && (
                    <button
                      onClick={handleStartWork}
                      disabled={busy}
                      className="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Start Work
                    </button>
                  )}
                  {canResolve && (
                    <button
                      onClick={openResolveModal}
                      disabled={busy}
                      className="w-full px-4 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Mark Resolved
                    </button>
                  )}
                  {canVerify && (
                    <div className="space-y-3">
                      <button
                        onClick={() => handleVerify(true)}
                        disabled={busy}
                        className="w-full px-4 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
                      >
                        ✓ Verify & Close
                      </button>
                      <button
                        onClick={() => handleVerify(false)}
                        disabled={busy}
                        className="w-full px-4 py-2.5 border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 text-sm font-medium rounded-lg transition-colors"
                      >
                        Reopen
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Resolve Proof Modal (reuses the SupervisorTaskList pattern) */}
      {resolveOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
          onClick={() => setResolveOpen(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-green-50 to-emerald-50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">Mark as Resolved</h3>
                  <p className="text-xs text-gray-500">Upload proof of resolution</p>
                </div>
              </div>
              <button
                onClick={() => setResolveOpen(false)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Proof Image <span className="text-red-500">*</span>
                </label>
                <div className={`relative border-2 border-dashed rounded-lg p-5 text-center transition-colors ${
                  proofPreview
                    ? "border-green-300 bg-green-50"
                    : imageError
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 hover:border-gray-400"
                }`}>
                  {proofPreview ? (
                    <div className="relative inline-block">
                      <img src={proofPreview} alt="Proof" className="max-h-40 rounded-lg mx-auto" />
                      <button
                        type="button"
                        onClick={() => { setProofImage(null); setProofPreview(null); }}
                        className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow-sm"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <div className="pointer-events-none">
                      <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <p className="mt-2 text-sm text-gray-500">Click to upload proof image</p>
                      <p className="text-xs text-gray-400 mt-1">PNG, JPG up to 5MB</p>
                    </div>
                  )}
                  {!proofPreview && (
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleProofImageChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  )}
                </div>
                {!proofPreview && (
                  <button
                    type="button"
                    onClick={() => setShowCamera(true)}
                    className="mt-3 w-full px-4 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white text-sm font-medium rounded-lg transition-all flex items-center justify-center gap-2 shadow-sm"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Take Photo
                  </button>
                )}
                {imageError && (
                  <p className="mt-1.5 text-sm text-red-500">{imageError}</p>
                )}
              </div>
              <CameraCapture
                isOpen={showCamera}
                onClose={() => setShowCamera(false)}
                onCapture={(imageData) => {
                  setProofPreview(imageData);
                  setProofImage(imageData);
                  setImageError("");
                }}
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Resolution Note <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe how the issue was resolved..."
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all resize-none text-sm"
                />
              </div>
            </div>

            <div className="flex gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
              <button
                onClick={() => setResolveOpen(false)}
                disabled={busy}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveSubmit}
                disabled={busy}
                className="flex-1 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {busy ? "Submitting..." : "Submit & Resolve"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IssueDetails;
