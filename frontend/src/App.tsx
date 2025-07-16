import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './contexts/AuthContext';
import { SidebarProvider } from './contexts/SidebarContext';
import Header from './components/Header';
import Landing from './pages/Landing';
import TravelRequest from './pages/TravelRequest';
import UnifiedTravelRequest from './pages/UnifiedTravelRequest';
import Trips from './pages/Trips';
import Profile from './pages/Profile';
import ProfileSettings from './pages/ProfileSettings';
import Travelers from './pages/Travelers';
import DebugSession from './pages/DebugSession';
import { configService } from './services/configService';
import './utils/sessionDebugger'; // Initialize session debugger
import './styles/App.css';
import './styles/landing.css';

const App: React.FC = () => {
  const [googleClientId, setGoogleClientId] = useState<string>('');

  useEffect(() => {
    // Load Google Client ID from environment
    const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '55013767303-slk94mloce0s2l4ipqdftbtobflppksf.apps.googleusercontent.com';
    setGoogleClientId(clientId);
  }, []);

  if (!googleClientId) {
    return <div>Loading...</div>;
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <AuthProvider>
        <SidebarProvider>
          <Router>
            <div className="App">
              <Header />
              <main className="main-content">
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/chat" element={<TravelRequest />} />
                  <Route path="/chat/:sessionId" element={<UnifiedTravelRequest />} />
                  <Route path="/trips" element={<Trips />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/profile/settings" element={<ProfileSettings />} />
                  <Route path="/travelers" element={<Travelers />} />
                  <Route path="/debug-session" element={<DebugSession />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </main>
            </div>
          </Router>
        </SidebarProvider>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
};

export default App;