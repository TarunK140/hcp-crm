import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LogInteractionPage from './pages/LogInteractionPage.jsx';

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <div className="app-logo-mark">🩺</div>
          <div>
            <h1>AI-First CRM — HCP Module</h1>
          </div>
        </div>
        <div className="subtitle">Field Rep Workspace</div>
      </header>

      <Routes>
        <Route path="/" element={<LogInteractionPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
