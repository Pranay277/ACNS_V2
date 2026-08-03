import React, { useState, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import NotificationBell from './NotificationBell';
import { signOutUser } from '../services/auth';

const NavbarUser = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const userEmail = useMemo(() => {
    try {
      const session = localStorage.getItem('session_user');
      if (session) {
        const data = JSON.parse(session);
        return data.email || 'user@campus.edu';
      }
    } catch {}
    return 'user@campus.edu';
  }, []);

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    signOutUser();
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/user" className="flex items-center gap-2">
            <span className="text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
              SCIARS
            </span>
            <span className="px-3 py-1 text-base font-bold bg-primary-100 text-primary-700 rounded uppercase tracking-wide">
              User
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            <Link
              to="/user"
              className={`relative px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/user')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/user/navigate"
              className={`relative px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/user/navigate')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              Navigate
            </Link>
            <Link
              to="/user/leaderboard"
              className={`relative px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/user/leaderboard')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              Leaderboard
            </Link>
            <Link
              to="/report"
              className={`relative px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105 hover:shadow-sm ${
                isActive('/report')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100'
              }`}
            >
              Report Issue
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <NotificationBell userId={userEmail} />
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

export default NavbarUser;
