import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AdminPanel from './components/AdminPanel';
import ClientLanding from './components/ClientLanding';
import QRAssistantPage from './components/QRAssistantPage'; // Legacy component
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Admin Panel Route */}
          <Route path="/admin" element={<AdminPanel />} />
          
          {/* Client Landing Routes */}
          <Route path="/client/:unique_url" element={<ClientLanding />} />
          
          {/* Legacy Route - redirect to admin */}
          <Route path="/" element={<Navigate to="/admin" replace />} />
          
          {/* Legacy QR Assistant Page (keeping for compatibility) */}
          <Route path="/legacy" element={<QRAssistantPage />} />
          
          {/* Catch all - redirect to admin */}
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;