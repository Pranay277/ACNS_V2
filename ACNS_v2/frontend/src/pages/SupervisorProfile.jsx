import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { getSupervisor, updateMyProfile } from '../services/api';
import { SMS_LANGUAGE_OPTIONS, DEFAULT_SMS_LANGUAGE } from '../constants/languages';

const inputCls = (readOnly = false) =>
  `w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 ${
    readOnly ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : 'bg-white text-gray-900'
  }`;

export default function SupervisorProfile() {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState(null);
  const [error, setError] = useState('');

  const notify = (message, isError = false) => setFlash({ message, isError });

  const errorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    if (detail && typeof detail === 'object' && detail.message) return detail.message;
    if (typeof detail === 'string') return detail;
    return fallback;
  };

  useEffect(() => {
    let activeSession = null;
    try {
      const s = JSON.parse(localStorage.getItem('session_supervisor') || '{}');
      if (s.email) activeSession = s;
    } catch {}
    if (!activeSession) {
      navigate('/login');
      return;
    }
    setSession(activeSession);

    (async () => {
      try {
        const uid = activeSession.uid || activeSession.email;
        const res = await getSupervisor(uid);
        const p = res.data?.supervisor;
        if (!p) throw new Error('Profile not found.');
        setProfile(p);
        setForm({
          displayName: p.displayName || '',
          phoneNumber: p.phoneNumber || '',
          preferredLanguage: p.preferredLanguage || DEFAULT_SMS_LANGUAGE,
        });
      } catch (err) {
        notify(errorMessage(err, 'Failed to load your profile.'), true);
      } finally {
        setLoading(false);
      }
    })();
  }, [navigate]);

  const setField = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
    setError('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.displayName.trim()) return setError('Full name is required.');

    setSaving(true);
    try {
      const uid = session.uid || session.email;
      const res = await updateMyProfile(uid, {
        displayName: form.displayName.trim(),
        phoneNumber: form.phoneNumber.trim() || null,
        preferredLanguage: form.preferredLanguage,
      });
      const updated = res.data?.supervisor;
      setProfile(updated);
      setForm({
        displayName: updated.displayName || '',
        phoneNumber: updated.phoneNumber || '',
        preferredLanguage: updated.preferredLanguage || DEFAULT_SMS_LANGUAGE,
      });
      localStorage.setItem(
        'session_supervisor',
        JSON.stringify({ ...session, name: updated.displayName })
      );
      notify('Profile updated. Future SMS notifications will use your new phone number and language.');
    } catch (err) {
      setError(errorMessage(err, 'Failed to update profile.'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center py-24">
          <div className="w-10 h-10 border-b-2 border-indigo-500 rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!form) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <p className="font-medium text-gray-500">Could not load your profile.</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Update your personal information. SMS notifications automatically use your phone number and preferred language.
          </p>
        </div>

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

        <form onSubmit={handleSave} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-indigo-500 flex items-center justify-center text-lg font-bold text-white shrink-0">
              {(profile?.displayName || profile?.email || '?').charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-lg font-semibold text-gray-900 truncate">{profile?.displayName || '—'}</p>
              <p className="text-sm text-gray-500 truncate">{profile?.department || 'Supervisor'}</p>
            </div>
          </div>

          <div className="px-6 py-5 space-y-5">
            <Field label="Full Name">
              <input type="text" value={form.displayName} onChange={setField('displayName')} className={inputCls(false)} />
            </Field>

            <Field label="Email">
              <input type="email" value={profile?.email || ''} readOnly className={inputCls(true)} />
              <p className="mt-1.5 text-xs text-gray-500">
                Login email. Only an administrator can change this.
              </p>
            </Field>

            <Field label="Phone Number">
              <input type="tel" placeholder="+91 98765 43210" value={form.phoneNumber} onChange={setField('phoneNumber')} className={inputCls(false)} />
            </Field>

            <Field label="Preferred SMS Language">
              <select value={form.preferredLanguage} onChange={setField('preferredLanguage')} className={inputCls(false)}>
                {SMS_LANGUAGE_OPTIONS.map((l) => (
                  <option key={l.code} value={l.code}>{l.label} ({l.hint})</option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-gray-500">
                Future SMS notifications will be sent in this language.
              </p>
            </Field>

            <Field label="Department">
              <input type="text" value={profile?.department || '—'} readOnly className={inputCls(true)} />
              <p className="mt-1.5 text-xs text-gray-500">
                Assigned by administrator.
              </p>
            </Field>

            <Field label="Role">
              <input type="text" value="Supervisor" readOnly className={inputCls(true)} />
            </Field>
          </div>

          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            {error ? (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600 flex items-start gap-2">
                <svg className="w-5 h-5 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            ) : (
              <span />
            )}
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
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
