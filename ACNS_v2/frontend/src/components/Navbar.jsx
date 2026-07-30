import React, { useState, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import NotificationBell from './NotificationBell';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const supervisorEmail = useMemo(() => {
    try {
      const session = localStorage.getItem('session_supervisor');
      if (session) {
        const data = JSON.parse(session);
        return data.email || 'supervisor@campus.edu';
      }
    } catch {}
    return 'supervisor@campus.edu';
  }, []);

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    localStorage.removeItem('session_supervisor');
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/supervisor" className="text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
            SCIARS
          </Link>

          <div className="hidden md:flex items-center gap-6">
            <Link
              to="/supervisor"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/supervisor') && !location.search.includes('filter=resolved')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              Supervisor Dashboard
            </Link>
            <Link
              to="/supervisor?filter=resolved"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/supervisor') && location.search.includes('filter=resolved')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              All Resolved Issues
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <NotificationBell userId={supervisorEmail} />
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              aria-label="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
