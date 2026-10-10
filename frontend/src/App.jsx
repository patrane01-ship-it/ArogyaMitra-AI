import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import TimelinePage from './pages/TimelinePage';
import RemindersPage from './pages/RemindersPage';
import DoctorReportPage from './pages/DoctorReportPage';
import RecordDetailPage from './pages/RecordDetailPage';
import SharePage from './pages/SharePage';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [shareToken, setShareToken] = useState(null);

  // Check URL for /share/{token}
  useEffect(() => {
    const path = window.location.pathname;
    const match = path.match(/^\/share\/([^/]+)/);
    if (match && match[1]) {
      setShareToken(match[1]);
    }
  }, []);

  // If viewing a share link, show isolated public consultation view
  if (shareToken) {
    return <SharePage token={shareToken} />;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      <main className="flex-1 pb-16">
        {activePage === 'dashboard' && (
          <DashboardPage
            setActivePage={setActivePage}
            setSelectedRecordId={setSelectedRecordId}
          />
        )}
        {activePage === 'upload' && <UploadPage setActivePage={setActivePage} />}
        {activePage === 'timeline' && <TimelinePage />}
        {activePage === 'reminders' && <RemindersPage />}
        {activePage === 'report' && <DoctorReportPage />}
        {activePage === 'detail' && (
          <RecordDetailPage
            recordId={selectedRecordId}
            setActivePage={setActivePage}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200/80 bg-white/50 py-4 text-center text-xs text-gray-500">
        <p>
          ArogyaMitra AI — Agentic Personal Health Intelligence • AES-256-GCM Encrypted At-Rest
        </p>
      </footer>
    </div>
  );
}
