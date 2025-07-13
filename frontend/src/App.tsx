import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { SidebarProvider } from './contexts/SidebarContext';
import Header from './components/Header';
import TravelRequest from './pages/TravelRequest';
import UnifiedTravelRequest from './pages/UnifiedTravelRequest';
import Trips from './pages/Trips';
import Profile from './pages/Profile';
import Travelers from './pages/Travelers';
import './styles/App.css';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <SidebarProvider>
        <Router>
          <div className="App">
            <Header />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Navigate to="/chat" replace />} />
                <Route path="/chat" element={<TravelRequest />} />
                <Route path="/chat/:sessionId" element={<UnifiedTravelRequest />} />
                <Route path="/trips" element={<Trips />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/travelers" element={<Travelers />} />
                <Route path="*" element={<Navigate to="/chat" replace />} />
              </Routes>
            </main>
          </div>
        </Router>
      </SidebarProvider>
    </AuthProvider>
  );
};

export default App;