import { useState, useLayoutEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import CreateDocument from './pages/CreateDocument.jsx';
import SecureViewer from './pages/SecureViewer.jsx';
import LeakDetection from './pages/LeakDetection.jsx';
import { authService } from './services/authService.js';
import ThemeToggle from './components/ThemeToggle.jsx';

function PrivateRoute({ children }) {
  return authService.isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  return (
    <>
      <div style={{ position: 'fixed', top: 20, right: 20, zindex: 2000 }}>
        <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
      </div>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/create" element={<PrivateRoute><CreateDocument /></PrivateRoute>} />
        <Route path="/view/:token" element={<SecureViewer />} />
        <Route path="/leak-detect" element={<PrivateRoute><LeakDetection /></PrivateRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}
