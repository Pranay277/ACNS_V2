import React, { useEffect, useState } from 'react';
import { getIssues } from '../services/api';
import NavbarAdmin from '../components/NavbarAdmin';

const STATUS_CONFIG = {
  Open:         { bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-200',    dot: 'bg-red-500'    },
  'In Progress':{ bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-200', dot: 'bg-yellow-500' },
  Resolved:     { bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-200',  dot: 'bg-green-500'  },
  Closed:       { bg: 'bg-gray-100',   text: 'text-gray-600',   border: 'border-gray-200',   dot: 'bg-gray-400'   },
};

const FILTERS = ['All', 'Open', 'In Progress', 'Resolved', 'Closed'];

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
  { value: 'status', label: 'By Status' },
  { value: 'category', label: 'By Category' },
  { value: 'reports', label: 'Most Reports' },
];

export default function AdminIssues() {
  const [issues, setIssues]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [filter, setFilter]           = useState('All');
  const [sort, setSort]               = useState('newest');
  const [search, setSearch]           = useState('');
  const [expandedId, setExpandedId]   = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getIssues({ role: 'admin' });
        setIssues(Array.isArray(res.data) ? res.data : []);
      } catch {
        setIssues([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // ── Filter ──────────────────────────────────────────────────────────────
  const filtered = issues.filter((issue) => {
    const matchStatus = filter === 'All' || issue.status === filter;
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      issue.category?.toLowerCase().includes(q) ||
      issue.description?.toLowerCase().includes(q) ||
      issue.location?.text?.toLowerCase().includes(q) ||
      issue.userId?.toLowerCase().includes(q);
    return matchStatus && matchSearch;
  });

  // ── Sort ────────────────────────────────────────────────────────────────
  const sorted = [...filtered].sort((a, b) => {
    if (sort === 'newest') return new Date(b.createdAt) - new Date(a.createdAt);
    if (sort === 'oldest') return new Date(a.createdAt) - new Date(b.createdAt);
    if (sort === 'status') return (a.status || '').localeCompare(b.status || '');
    if (sort === 'category') return (a.category || '').localeCompare(b.category || '');
    if (sort === 'reports') return (b.reportCount || 1) - (a.reportCount || 1);
    return 0;
  });

  // ── Stats ───────────────────────────────────────────────────────────────
  const stats = [
    { label: 'Total',       value: issues.length,                                          color: 'bg-indigo-500' },
    { label: 'Open',        value: issues.filter(i => i.status === 'Open').length,         color: 'bg-red-500'    },
    { label: 'In Progress', value: issues.filter(i => i.status === 'In Progress').length,  color: 'bg-yellow-500' },
    { label: 'Resolved',    value: issues.filter(i => i.status === 'Resolved').length,     color: 'bg-green-500'  },
  ];

  const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const getCategoryCount = () => {
    const counts = {};
    issues.forEach(issue => {
      const cat = issue.category || 'Unknown';
      counts[cat] = (counts[cat] || 0) + 1;
    });
    return counts;
  };

  const categoryCount = getCategoryCount();

  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarAdmin />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Page title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">All Reported Issues</h1>
          <p className="text-sm text-gray-500 mt-0.5">Every issue submitted across all users — sorted, filtered, and searchable.</p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {stats.map((s) => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3 shadow-sm">
              <div className={`${s.color} w-3 h-3 rounded-full flex-shrink-0`} />
              <div>
                <p className="text-xs text-gray-500 font-medium">{s.label}</p>
                <p className="text-xl font-bold text-gray-900">{s.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Controls: search + filter + sort */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4 flex flex-col sm:flex-row gap-3">

          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by category, description, location, user..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          {/* Sort */}
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        {/* Filter tabs */}
        <div className="flex flex-wrap gap-2 mb-4">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-all ${
                filter === f
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              {f}
              {f !== 'All' && (
                <span className="ml-1.5 text-xs opacity-75">
                  ({issues.filter(i => i.status === f).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Issues table */}
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-10 h-10 border-b-2 border-indigo-500 rounded-full animate-spin" />
          </div>
        ) : sorted.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
            <svg className="mx-auto w-12 h-12 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="font-medium text-gray-500">No issues found</p>
            <p className="text-sm mt-1">Try changing the filter or search query.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

            {/* Table header */}
            <div className="hidden md:grid grid-cols-12 gap-4 px-5 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <div className="col-span-1">#</div>
              <div className="col-span-2">Category</div>
              <div className="col-span-1">Reports</div>
              <div className="col-span-2">Description</div>
              <div className="col-span-2">Location</div>
              <div className="col-span-1">Status</div>
              <div className="col-span-2">Reported By</div>
              <div className="col-span-1">Date</div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-gray-100">
              {sorted.map((issue, index) => {
                const sc = STATUS_CONFIG[issue.status] || STATUS_CONFIG.Closed;
                const isExpanded = expandedId === issue.id;

                return (
                  <div key={issue.id || index}>
                    {/* Main row */}
                    <div
                      className="grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4 px-5 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => setExpandedId(isExpanded ? null : issue.id)}
                    >
                      {/* # */}
                      <div className="hidden md:flex col-span-1 items-center text-sm text-gray-400 font-mono">
                        {index + 1}
                      </div>

                      {/* Category */}
                      <div className="md:col-span-2 flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-800">{issue.category || '—'}</span>
                      </div>

                      {/* Reports count */}
                      <div className="md:col-span-1 flex items-center">
                        <span className="inline-flex items-center justify-center min-w-[28px] px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-700">
                          {issue.reportCount || 1}
                        </span>
                      </div>

                      {/* Description */}
                      <div className="md:col-span-2 flex items-center">
                        <p className="text-sm text-gray-600 line-clamp-2">{issue.description || '—'}</p>
                      </div>

                      {/* Location */}
                      <div className="md:col-span-2 flex items-center gap-1 text-sm text-gray-500">
                        <svg className="w-3.5 h-3.5 flex-shrink-0 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span className="truncate">{issue.location?.text || '—'}</span>
                      </div>

                      {/* Status badge */}
                      <div className="md:col-span-1 flex items-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${sc.bg} ${sc.text} ${sc.border}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                          {issue.status}
                        </span>
                      </div>

                      {/* Reported by */}
                      <div className="md:col-span-2 flex items-center">
                        <p className="text-xs text-gray-500 truncate">{issue.userId || '—'}</p>
                      </div>

                      {/* Date */}
                      <div className="md:col-span-1 flex items-center">
                        <p className="text-xs text-gray-400">{issue.createdAt ? new Date(issue.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</p>
                      </div>
                    </div>

                    {/* Expanded detail row */}
                    {isExpanded && (
                      <div className="bg-indigo-50 border-t border-indigo-100 px-5 py-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Full Description</p>
                          <p className="text-sm text-gray-700 leading-relaxed">{issue.description || '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Assigned To</p>
                          <p className="text-sm text-gray-700">{issue.assignedTo || '—'}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Reported On</p>
                          <p className="text-sm text-gray-700">{formatDate(issue.createdAt)}</p>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Coordinates</p>
                          <p className="text-sm text-gray-700 font-mono">
                            {issue.location?.lat && issue.location?.lng
                              ? `${issue.location.lat.toFixed(5)}, ${issue.location.lng.toFixed(5)}`
                              : '—'}
                          </p>
                        </div>
                        {issue.imageUrl && (
                          <div className="sm:col-span-2 lg:col-span-4">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Reported Image</p>
                            <img src={issue.imageUrl} alt="Issue" className="max-h-48 rounded-lg border border-gray-200 object-cover" />
                          </div>
                        )}
                        {(issue.status === 'In Progress' || issue.status === 'Resolved' || issue.status === 'Closed') && (
                          <div className="sm:col-span-2 lg:col-span-4 border-t border-indigo-200 pt-4 mt-2">
                            <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-3">Supervisor Details</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                              <div>
                                <p className="text-xs text-gray-500 mb-1">Supervisor Name</p>
                                <p className="text-sm font-medium text-gray-800">{issue.supervisorName || '—'}</p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-500 mb-1">Supervisor Email</p>
                                <p className="text-sm text-gray-700">{issue.supervisorEmail || '—'}</p>
                              </div>
                              {issue.supervisorDescription && (
                                <div className="sm:col-span-2">
                                  <p className="text-xs text-gray-500 mb-1">Description</p>
                                  <p className="text-sm text-gray-700">{issue.supervisorDescription}</p>
                                </div>
                              )}
                              {issue.supervisorPhoto && (
                                <div>
                                  <p className="text-xs text-gray-500 mb-1">Supervisor Photo</p>
                                  <img src={issue.supervisorPhoto} alt="Supervisor" className="w-16 h-16 rounded-full border border-gray-300 object-cover" />
                                </div>
                              )}
                              {issue.proofImageUrl && (
                                <div>
                                  <p className="text-xs text-gray-500 mb-1">Proof Photo</p>
                                  <img src={issue.proofImageUrl} alt="Proof" className="max-h-24 rounded-lg border border-green-200 object-cover" />
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        {issue.status === 'Resolved' && issue.proofImageUrl && !issue.supervisorPhoto && (
                          <div className="sm:col-span-2 lg:col-span-4">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Resolution Proof</p>
                            <img src={issue.proofImageUrl} alt="Proof" className="max-h-48 rounded-lg border border-green-200 object-cover" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Footer count */}
            <div className="px-5 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-400">
              Showing {sorted.length} of {issues.length} issues
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
