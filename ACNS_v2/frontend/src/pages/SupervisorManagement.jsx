import React, { useEffect, useState } from 'react';
import NavbarAdmin from '../components/NavbarAdmin';
import {
  getSupervisors,
  createSupervisor,
  updateSupervisor,
  changeSupervisorEmail,
  deactivateSupervisor,
  activateSupervisor,
  deleteSupervisor,
  resetSupervisorPassword,
} from '../services/api';
import { SMS_LANGUAGE_OPTIONS, DEFAULT_SMS_LANGUAGE } from '../constants/languages';
import { DEPARTMENT_OPTIONS } from '../constants/departments';

const STATUS_FILTERS = ['All', 'Active', 'Inactive'];

const emptyAddForm = {
  displayName: '',
  email: '',
  department: '',
  phoneNumber: '',
  preferredLanguage: DEFAULT_SMS_LANGUAGE,
  password: '',
  setPassword: false,
};

export default function SupervisorManagement() {
  const [supervisors, setSupervisors] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  const [addOpen, setAddOpen] = useState(false);
  const [addForm, setAddForm] = useState(emptyAddForm);
  const [addError, setAddError] = useState('');
  const [addSaving, setAddSaving] = useState(false);
  const [createdPassword, setCreatedPassword] = useState(null);

  const [editTarget, setEditTarget] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [editError, setEditError] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  const [resetTarget, setResetTarget] = useState(null);
  const [resetForm, setResetForm] = useState({ newPassword: '', confirm: '' });
  const [resetError, setResetError] = useState('');
  const [resetSaving, setResetSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteError, setDeleteError] = useState('');
  const [deleteSaving, setDeleteSaving] = useState(false);

  const [flash, setFlash] = useState(null);

  const notify = (message, isError = false) =>
    setFlash({ message, isError });

  const errorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    if (detail && typeof detail === 'object' && detail.message) return detail.message;
    if (typeof detail === 'string') return detail;
    return fallback;
  };

  const identity = (s) => s?.uid || s?.userId || s?.email;

  const load = async () => {
    try {
      const res = await getSupervisors({ includeInactive: true });
      setSupervisors(Array.isArray(res.data?.supervisors) ? res.data.supervisors : []);
    } catch (err) {
      notify(errorMessage(err, 'Failed to load supervisors.'), true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ── Filtering ──────────────────────────────────────────────────────────
  const departments = ['All', ...new Set(supervisors.map((s) => s.department).filter(Boolean))];

  const filtered = supervisors.filter((s) => {
    const q = search.trim().toLowerCase();
    const matchSearch =
      !q ||
      (s.displayName || '').toLowerCase().includes(q) ||
      (s.email || '').toLowerCase().includes(q) ||
      (s.department || '').toLowerCase().includes(q) ||
      (s.phoneNumber || '').toLowerCase().includes(q);
    const matchDept = departmentFilter === 'All' || s.department === departmentFilter;
    const matchStatus =
      statusFilter === 'All' ||
      (statusFilter === 'Active' && s.isActive !== false) ||
      (statusFilter === 'Inactive' && s.isActive === false);
    return matchSearch && matchDept && matchStatus;
  });

  const stats = {
    Total: supervisors.length,
    Active: supervisors.filter((s) => s.isActive !== false).length,
    Inactive: supervisors.filter((s) => s.isActive === false).length,
  };

  // ── Add Supervisor ─────────────────────────────────────────────────────
  const openAdd = () => {
    setAddForm(emptyAddForm);
    setAddError('');
    setCreatedPassword(null);
    setAddOpen(true);
  };

  const setAddField = (field) => (e) => {
    setAddForm({ ...addForm, [field]: e.target.value });
    setAddError('');
  };

  const generatePassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%';
    const rand = new Uint32Array(14);
    crypto.getRandomValues(rand);
    const pw = Array.from(rand, (n) => chars[n % chars.length]).join('') + 'A1!';
    setAddForm({ ...addForm, password: pw });
    setAddError('');
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setAddError('');
    if (!addForm.displayName.trim()) return setAddError('Full name is required.');
    if (!addForm.email.trim()) return setAddError('Email is required.');
    if (!addForm.department) return setAddError('Department is required.');

    setAddSaving(true);
    try {
      const payload = {
        email: addForm.email.trim(),
        displayName: addForm.displayName.trim(),
        department: addForm.department,
        phoneNumber: addForm.phoneNumber.trim() || null,
        preferredLanguage: addForm.preferredLanguage,
      };
      if (addForm.setPassword && addForm.password) payload.password = addForm.password;

      const res = await createSupervisor(payload);
      const supervisor = res.data?.supervisor || {};
      if (supervisor.temporaryPassword) setCreatedPassword(supervisor.temporaryPassword);
      notify(`Supervisor ${supervisor.displayName || ''} created successfully.`);
      setAddForm(emptyAddForm);
      await load();
    } catch (err) {
      setAddError(errorMessage(err, 'Failed to create supervisor.'));
    } finally {
      setAddSaving(false);
    }
  };

  // ── Edit Supervisor ────────────────────────────────────────────────────
  const openEdit = (s) => {
    setEditTarget(s);
    setEditForm({
      displayName: s.displayName || '',
      email: s.email || '',
      department: s.department || '',
      phoneNumber: s.phoneNumber || '',
      preferredLanguage: s.preferredLanguage || DEFAULT_SMS_LANGUAGE,
      isActive: s.isActive !== false,
    });
    setEditError('');
  };

  const setEditField = (field) => (e) => {
    setEditForm({ ...editForm, [field]: e.target.value });
    setEditError('');
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    setEditError('');
    if (!editForm.displayName.trim()) return setEditError('Full name is required.');
    if (!editForm.department) return setEditError('Department is required.');
    if (!editForm.email.trim()) return setEditError('Login email is required.');

    const uid = identity(editTarget);
    const emailChanged =
      editForm.email.trim().toLowerCase() !== (editTarget.email || '').trim().toLowerCase();

    if (emailChanged) {
      const confirmed = window.confirm(
        "This changes the supervisor's login email.\n\nThe supervisor must use the new email for future logins."
      );
      if (!confirmed) return;
    }

    setEditSaving(true);
    try {
      const statusChanged = editForm.isActive !== (editTarget.isActive !== false);
      const updates = {
        displayName: editForm.displayName.trim(),
        department: editForm.department,
        phoneNumber: editForm.phoneNumber.trim() || null,
        preferredLanguage: editForm.preferredLanguage,
      };
      if (emailChanged) {
        await changeSupervisorEmail(uid, { newEmail: editForm.email.trim() });
      }
      await updateSupervisor(uid, updates);
      if (statusChanged) {
        if (editForm.isActive) await activateSupervisor(uid);
        else await deactivateSupervisor(uid);
      }
      notify(`Supervisor ${editForm.displayName || editTarget.email} updated.`);
      setEditTarget(null);
      await load();
    } catch (err) {
      setEditError(errorMessage(err, 'Failed to update supervisor.'));
    } finally {
      setEditSaving(false);
    }
  };

  // ── Quick activate / deactivate ────────────────────────────────────────
  const handleToggleActive = async (s) => {
    const activating = s.isActive === false;
    const verb = activating ? 'activate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${verb} ${s.displayName || s.email}?`)) return;
    try {
      if (activating) await activateSupervisor(identity(s));
      else await deactivateSupervisor(identity(s));
      notify(`Supervisor ${s.email} ${activating ? 'activated' : 'deactivated'}.`);
      await load();
    } catch (err) {
      notify(errorMessage(err, `Failed to ${verb} supervisor.`), true);
    }
  };

  // ── Reset password ─────────────────────────────────────────────────────
  const setResetField = (field) => (e) => {
    setResetForm({ ...resetForm, [field]: e.target.value });
    setResetError('');
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setResetError('');
    if (resetForm.newPassword.length < 6) return setResetError('Password must be at least 6 characters.');
    if (resetForm.newPassword !== resetForm.confirm) return setResetError('Passwords do not match.');
    setResetSaving(true);
    try {
      await resetSupervisorPassword(identity(resetTarget), { newPassword: resetForm.newPassword });
      notify(`Password reset for ${resetTarget.email}.`);
      setResetTarget(null);
      setResetForm({ newPassword: '', confirm: '' });
    } catch (err) {
      setResetError(errorMessage(err, 'Failed to reset password.'));
    } finally {
      setResetSaving(false);
    }
  };

  // ── Delete Supervisor ──────────────────────────────────────────────────
  const handleDelete = async () => {
    setDeleteError('');
    setDeleteSaving(true);
    try {
      await deleteSupervisor(identity(deleteTarget));
      notify(`Supervisor ${deleteTarget.email} deleted.`);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      setDeleteError(errorMessage(err, 'Failed to delete supervisor.'));
    } finally {
      setDeleteSaving(false);
    }
  };

  const inputCls = (hasError) =>
    `w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400 ${
      hasError ? 'border-red-300' : 'border-gray-200'
    }`;

  return (
    <div className="min-h-screen bg-gray-50">
      <NavbarAdmin />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Supervisor Management</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Create, edit, and manage supervisor accounts. SMS assignments follow department routing.
            </p>
          </div>
          <button
            onClick={openAdd}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all duration-200 hover:scale-[1.03]"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Supervisor
          </button>
        </div>

        {/* Flash */}
        {flash && (
          <div
            className={`mb-4 px-4 py-3 rounded-lg border text-sm flex items-start gap-2 ${
              flash.isError
                ? 'bg-red-50 border-red-200 text-red-600'
                : 'bg-emerald-50 border-emerald-200 text-emerald-700'
            }`}
          >
            <svg className="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{flash.message}</span>
            <button className="ml-auto text-gray-400 hover:text-gray-600" onClick={() => setFlash(null)}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {Object.entries(stats).map(([label, value]) => (
            <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <p className="text-xs text-gray-500 font-medium">{label}</p>
              <p className="text-xl font-bold text-gray-900">{value}</p>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4 flex flex-col lg:flex-row gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by name, email, department, phone..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            {departments.map((d) => (
              <option key={d} value={d}>{d === 'All' ? 'All Departments' : d}</option>
            ))}
          </select>
        </div>

        {/* Status filter tabs */}
        <div className="flex flex-wrap gap-2 mb-4">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-all ${
                statusFilter === f
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              {f}
              <span className="ml-1.5 text-xs opacity-75">
                {f === 'All' ? supervisors.length : f === 'Active' ? stats.Active : stats.Inactive}
              </span>
            </button>
          ))}
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-10 h-10 border-b-2 border-indigo-500 rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
            <svg className="mx-auto w-12 h-12 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4zm6-1.13a4 4 0 10-4-4 4 4 0 004 4z" />
            </svg>
            <p className="font-medium text-gray-500">No supervisors found</p>
            <p className="text-sm mt-1">Try changing the filters or search query.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="hidden md:grid grid-cols-12 gap-4 px-5 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <div className="col-span-1">#</div>
              <div className="col-span-3">Name</div>
              <div className="col-span-2">Department</div>
              <div className="col-span-2">Phone</div>
              <div className="col-span-1">Language</div>
              <div className="col-span-1">Status</div>
              <div className="col-span-2">Actions</div>
            </div>

            <div className="divide-y divide-gray-100">
              {filtered.map((s, index) => {
                const active = s.isActive !== false;
                return (
                  <div key={s.uid || s.userId || index} className="grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                    <div className="hidden md:flex col-span-1 items-center text-sm text-gray-400 font-mono">{index + 1}</div>

                    <div className="md:col-span-3 flex items-center gap-3 min-w-0">
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0 ${active ? 'bg-indigo-500' : 'bg-gray-400'}`}>
                        {(s.displayName || s.email || '?').charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-800 truncate">{s.displayName || '—'}</p>
                        <p className="text-xs text-gray-500 truncate">{s.email}</p>
                      </div>
                    </div>

                    <div className="md:col-span-2 flex items-center">
                      <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                        {s.department || '—'}
                      </span>
                    </div>

                    <div className="md:col-span-2 flex items-center text-sm text-gray-600">{s.phoneNumber || '—'}</div>

                    <div className="md:col-span-1 flex items-center text-xs text-gray-500 uppercase">{s.preferredLanguage || 'en'}</div>

                    <div className="md:col-span-1 flex items-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${
                        active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-gray-100 text-gray-500 border-gray-200'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                        {active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    <div className="md:col-span-2 flex flex-wrap items-center gap-2">
                      <button onClick={() => openEdit(s)} className="px-2.5 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors">Edit</button>
                      <button onClick={() => handleToggleActive(s)} className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${active ? 'text-amber-600 bg-amber-50 hover:bg-amber-100' : 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100'}`}>
                        {active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button onClick={() => { setResetTarget(s); setResetForm({ newPassword: '', confirm: '' }); setResetError(''); }} className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">Reset PW</button>
                      <button onClick={() => { setDeleteTarget(s); setDeleteError(''); }} className="px-2.5 py-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors">Delete</button>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="px-5 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-400">
              Showing {filtered.length} of {supervisors.length} supervisors
            </div>
          </div>
        )}
      </div>

      {/* ── Add Supervisor modal ─────────────────────────────────────────── */}
      {addOpen && (
        <Modal title="Add Supervisor" onClose={() => setAddOpen(false)}>
          <form onSubmit={handleAdd} className="space-y-4">
            <Field label="Full Name" error={addError}>
              <input type="text" placeholder="Supervisor name" value={addForm.displayName} onChange={setAddField('displayName')} className={inputCls(false)} />
            </Field>
            <Field label="Personal Email">
              <input type="email" placeholder="name@example.com" value={addForm.email} onChange={setAddField('email')} className={inputCls(false)} />
            </Field>
            <Field label="Department">
              <select value={addForm.department} onChange={setAddField('department')} className={inputCls(false)}>
                <option value="">Select department</option>
                {DEPARTMENT_OPTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </Field>
            <Field label="Phone Number">
              <input type="tel" placeholder="+91 98765 43210" value={addForm.phoneNumber} onChange={setAddField('phoneNumber')} className={inputCls(false)} />
            </Field>
            <Field label="Preferred SMS Language">
              <select value={addForm.preferredLanguage} onChange={setAddField('preferredLanguage')} className={inputCls(false)}>
                {SMS_LANGUAGE_OPTIONS.map((l) => <option key={l.code} value={l.code}>{l.label} ({l.hint})</option>)}
              </select>
            </Field>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={addForm.setPassword} onChange={(e) => setAddForm({ ...addForm, setPassword: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                Set temporary password
              </label>
            </div>

            {addForm.setPassword ? (
              <div className="flex gap-2">
                <input type="text" value={addForm.password} onChange={setAddField('password')} placeholder="Temporary password" className={inputCls(false)} />
                <button type="button" onClick={generatePassword} className="px-3 py-2 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg whitespace-nowrap transition-colors">Generate</button>
              </div>
            ) : (
              <p className="text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                A temporary password will be generated automatically and shown once after creation.
              </p>
            )}

            {addError && <Alert message={addError} />}

            {createdPassword && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm">
                <p className="font-semibold text-amber-800 mb-1">Temporary password (shown once):</p>
                <div className="flex gap-2 items-center">
                  <code className="flex-1 px-2 py-1 bg-white border border-amber-200 rounded font-mono text-amber-900">{createdPassword}</code>
                  <button type="button" onClick={() => navigator.clipboard?.writeText(createdPassword)} className="px-2 py-1 text-xs text-amber-700 bg-amber-100 rounded">Copy</button>
                </div>
                <p className="text-xs text-amber-700 mt-1">Share this with the supervisor. The password can be reset anytime.</p>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setAddOpen(false)} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button type="submit" disabled={addSaving} className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed">
                {addSaving ? 'Creating...' : 'Create Supervisor'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* ── Edit Supervisor modal ────────────────────────────────────────── */}
      {editTarget && editForm && (
        <Modal title={`Edit Supervisor — ${editTarget.displayName || editTarget.email}`} onClose={() => setEditTarget(null)}>
          <form onSubmit={handleEdit} className="space-y-4">
            <Field label="Full Name">
              <input type="text" value={editForm.displayName} onChange={setEditField('displayName')} className={inputCls(false)} />
            </Field>
            <Field label="Login Email">
              <input type="email" value={editForm.email} onChange={setEditField('email')} className={inputCls(false)} />
              <p className="mt-1.5 text-xs text-gray-500">
                Changing the email updates the login email. The supervisor must use the new email for future logins. Their uid, department, phone, language, issue assignments and SMS are unchanged.
              </p>
            </Field>
            <Field label="Department">
              <select value={editForm.department} onChange={setEditField('department')} className={inputCls(false)}>
                <option value="">Select department</option>
                {DEPARTMENT_OPTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </Field>
            <Field label="Phone Number">
              <input type="tel" value={editForm.phoneNumber} onChange={setEditField('phoneNumber')} className={inputCls(false)} />
            </Field>
            <Field label="Preferred SMS Language">
              <select value={editForm.preferredLanguage} onChange={setEditField('preferredLanguage')} className={inputCls(false)}>
                {SMS_LANGUAGE_OPTIONS.map((l) => <option key={l.code} value={l.code}>{l.label} ({l.hint})</option>)}
              </select>
            </Field>

            <div className="flex items-center justify-between pt-1">
              <span className="text-sm text-gray-700">Account status</span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={editForm.isActive} onChange={(e) => setEditForm({ ...editForm, isActive: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
                <span className={`text-sm font-medium ${editForm.isActive ? 'text-emerald-600' : 'text-gray-400'}`}>
                  {editForm.isActive ? 'Active' : 'Inactive'}
                </span>
              </label>
            </div>

            {editError && <Alert message={editError} />}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setEditTarget(null)} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button type="submit" disabled={editSaving} className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed">
                {editSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* ── Reset password modal ─────────────────────────────────────────── */}
      {resetTarget && (
        <Modal title={`Reset Password — ${resetTarget.email}`} onClose={() => setResetTarget(null)}>
          <form onSubmit={handleReset} className="space-y-4">
            <Field label="New Password">
              <input type="password" value={resetForm.newPassword} onChange={setResetField('newPassword')} placeholder="At least 6 characters" className={inputCls(false)} />
            </Field>
            <Field label="Confirm Password">
              <input type="password" value={resetForm.confirm} onChange={setResetField('confirm')} placeholder="Re-enter new password" className={inputCls(false)} />
            </Field>
            {resetError && <Alert message={resetError} />}
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setResetTarget(null)} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
              <button type="submit" disabled={resetSaving} className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed">
                {resetSaving ? 'Resetting...' : 'Reset Password'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* ── Delete confirmation modal ────────────────────────────────────── */}
      {deleteTarget && (
        <Modal title="Delete Supervisor" onClose={() => setDeleteTarget(null)}>
          <p className="text-sm text-gray-700 mb-4">
            Are you sure you want to permanently delete{' '}
            <span className="font-semibold">{deleteTarget.displayName || deleteTarget.email}</span>{' '}
            ({deleteTarget.email})? This also removes their login account.
          </p>
          {deleteError ? (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600 mb-4">
              <p className="font-semibold mb-1">Deletion not allowed:</p>
              {deleteError}
            </div>
          ) : (
            <p className="text-xs text-gray-500 mb-4">
              Deletion is blocked while the supervisor still has Open or In Progress issues assigned.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <button onClick={() => setDeleteTarget(null)} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
            <button onClick={handleDelete} disabled={deleteSaving} className="px-4 py-2 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed">
              {deleteSaving ? 'Deleting...' : 'Delete Supervisor'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ── Small presentational helpers ─────────────────────────────────────────────

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" onClick={onClose}>
      <div
        className="relative w-full max-w-lg bg-white rounded-xl shadow-2xl p-6 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

function Alert({ message }) {
  return (
    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600 flex items-start gap-2">
      <svg className="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
      <span>{message}</span>
    </div>
  );
}
