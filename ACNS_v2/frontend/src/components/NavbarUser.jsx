import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import NotificationBell from './NotificationBell';

const NavbarUser = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/user" className="flex items-center gap-2">
            <span className="text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
              SCIARS
            </span>
            <span className="px-2 py-0.5 text-xs font-semibold bg-primary-100 text-primary-700 rounded uppercase tracking-wide">
              User
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            <Link
              to="/user"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/user')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/report"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/report')
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
              }`}
            >
              Report Issue
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <NotificationBell userId="user1@gmail.com" />
            <button 
              onClick={() => navigate('/')}
              className="p-2 text-gray-500 hover:text-red-600 transition-colors" 
              aria-label="Logout"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavbarUser;
