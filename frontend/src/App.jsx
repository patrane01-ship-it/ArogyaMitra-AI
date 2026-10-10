import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { FamilyProvider } from './context/FamilyContext';
import Navbar from './components/Navbar';
import AuthPage from './components/AuthPage';

// Import Pages
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import TimelinePage from './pages/TimelinePage';
import RemindersPage from './pages/RemindersPage';
import DoctorReportPage from './pages/DoctorReportPage';
import FamilyPage from './pages/FamilyPage';
import SubscriptionPage from './pages/SubscriptionPage';
import PredictionsPage from './pages/PredictionsPage';
import DoctorWorkspacePage from './pages/DoctorWorkspacePage';

function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) return null;
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function Layout({ children }) {
  const location = useLocation();
  const isDoctorView = location.pathname.startsWith('/doctor-view');

  if (isDoctorView) {
    return children;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#F8FAFC' }}>
      <Navbar />
      <main style={{ flex: 1, overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  );
}

function MainApp() {
  const { token, loading } = useAuth();

  if (loading) return null;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/doctor-view/:token" element={<DoctorWorkspacePage token={useLocation().pathname.split('/').pop()} />} />
        
        <Route path="/login" element={token ? <Navigate to="/" replace /> : <AuthPage onAuthenticated={() => {}} />} />
        
        <Route path="/*" element={
          <ProtectedRoute>
            <FamilyProvider>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/timeline" element={<TimelinePage />} />
                  <Route path="/reminders" element={<RemindersPage />} />
                  <Route path="/report" element={<DoctorReportPage />} />
                  <Route path="/family" element={<FamilyPage />} />
                  <Route path="/subscription" element={<SubscriptionPage />} />
                  <Route path="/predictions" element={<PredictionsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </FamilyProvider>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
