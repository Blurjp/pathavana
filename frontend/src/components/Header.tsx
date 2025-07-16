import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSidebar } from '../contexts/SidebarContext';
import { LoginModal } from './auth/LoginModalSimple';

const Header: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const { toggleSidebar, sidebarOpen } = useSidebar();
  const location = useLocation();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  const isActivePath = (path: string): boolean => {
    return location.pathname === path || location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    navigate('/');
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showUserMenu && !target.closest('.user-menu')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showUserMenu]);

  return (
    <>
    <header className="header">
      <div className="header-content">
        {/* Logo and Navigation */}
        <div className="header-left">
          <Link to="/" className="logo">
            <span className="logo-text">Pathavana</span>
          </Link>
          
          {isAuthenticated && (
            <nav className="nav-menu">
              <Link
                to="/chat"
                className={`nav-item ${isActivePath('/chat') ? 'active' : ''}`}
              >
                Chat
              </Link>
              <Link
                to="/trips"
                className={`nav-item ${isActivePath('/trips') ? 'active' : ''}`}
              >
                Trips
              </Link>
              <Link
                to="/travelers"
                className={`nav-item ${isActivePath('/travelers') ? 'active' : ''}`}
              >
                Travelers
              </Link>
            </nav>
          )}
        </div>

        {/* Right side controls */}
        <div className="header-right">
          {/* Sidebar toggle for search results */}
          {(isActivePath('/chat') || isActivePath('/trips')) && (
            <button
              onClick={toggleSidebar}
              className={`sidebar-toggle ${sidebarOpen ? 'active' : ''}`}
              aria-label="Toggle search results"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M3 6h18M3 12h18M3 18h18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          )}

          {/* User menu */}
          {isAuthenticated ? (
            <div className="user-menu">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="user-avatar"
                aria-label="User menu"
              >
                {user?.avatar ? (
                  <img src={user.avatar} alt={user?.full_name || 'User'} />
                ) : (
                  <div className="avatar-placeholder">
                    {user?.full_name?.charAt(0)?.toUpperCase() || 
                     user?.email?.charAt(0)?.toUpperCase() || 
                     'U'}
                  </div>
                )}
              </button>

              {showUserMenu && (
                <div className="user-menu-dropdown">
                  <div className="user-info">
                    <div className="user-name">{user?.full_name || 'User'}</div>
                    <div className="user-email">{user?.email || 'No email'}</div>
                  </div>
                  <hr />
                  <Link
                    to="/profile"
                    className="menu-item"
                    onClick={() => setShowUserMenu(false)}
                  >
                    Profile Settings
                  </Link>
                  <Link
                    to="/trips"
                    className="menu-item"
                    onClick={() => setShowUserMenu(false)}
                  >
                    My Trips
                  </Link>
                  <Link
                    to="/travelers"
                    className="menu-item"
                    onClick={() => setShowUserMenu(false)}
                  >
                    Travelers
                  </Link>
                  <hr />
                  <button
                    onClick={handleLogout}
                    className="menu-item logout"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <button 
                onClick={() => setShowLoginModal(true)} 
                className="btn-secondary"
              >
                Sign In
              </button>
              <button 
                onClick={() => setShowLoginModal(true)} 
                className="btn-primary"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </div>
    </header>

    {/* Login Modal */}
    <LoginModal
      isOpen={showLoginModal}
      onClose={() => setShowLoginModal(false)}
      onSuccess={() => {
        setShowLoginModal(false);
        navigate('/chat');
      }}
    />
    </>
  );
};

export default Header;