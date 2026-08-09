import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Activity, 
  UploadCloud, 
  TrendingUp, 
  CalendarClock, 
  FileText, 
  FileSpreadsheet, 
  ShieldCheck, 
  HeartHandshake, 
  Menu, 
  X,
  Search,
  LogOut,
  Brain
} from 'lucide-react';

// Components
import { Dashboard } from './components/Dashboard.tsx';
import { UploadCenter } from './components/UploadCenter.tsx';
import { TrendsTimeline } from './components/TrendsTimeline.tsx';
import { RemindersManager } from './components/RemindersManager.tsx';
import { DoctorPrep } from './components/DoctorPrep.tsx';
import { RecordsLog } from './components/RecordsLog.tsx';
import { RecordDetailPage } from './components/RecordDetailPage.tsx';
import { SharedView } from './components/SharedView.tsx';
import AIChatbot from './components/AIChatbot.tsx';

type TabType = 'dashboard' | 'upload' | 'timeline' | 'reminders' | 'report' | 'records' | 'chat';

export default function App() {
  const [currentHash, setCurrentHash] = useState(window.location.hash);
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [activeRecordId, setActiveRecordId] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [globalSearchTerm, setGlobalSearchTerm] = useState('');

  const handleLogout = () => {
    if (confirm('Are you sure you want to clear your current clinical session? This will reset all active states and clear local tokens.')) {
      localStorage.clear();
      sessionStorage.clear();
      
      // Clear standard session cookies
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i];
        const eqPos = cookie.indexOf("=");
        const name = eqPos > -1 ? cookie.substring(0, eqPos).trim() : cookie.trim();
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
      }

      // Reset states
      setActiveTab('dashboard');
      setActiveRecordId(null);
      setGlobalSearchTerm('');
      setMobileMenuOpen(false);

      alert('Session has been cleared. Application state has been reset successfully.');
    }
  };

  // Synchronize hash changes
  useEffect(() => {
    const handleHashChange = () => {
      setCurrentHash(window.location.hash);
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Parse share token from hash if visiting #/share/<token>
  const getShareToken = () => {
    const match = currentHash.match(/^#\/share\/([a-f0-9]+)$/i);
    return match ? match[1] : null;
  };

  const shareToken = getShareToken();

  // If visiting a shared clinical link, show the Shared View instantly
  if (shareToken) {
    return <SharedView token={shareToken} />;
  }

  const navItems = [
    { id: 'dashboard', label: 'Health Dashboard', icon: Activity },
    { id: 'chat', label: 'AI Health Companion', icon: Brain },
    { id: 'upload', label: 'Ingestion Center', icon: UploadCloud },
    { id: 'timeline', label: 'Bio-Marker Trends', icon: TrendingUp },
    { id: 'reminders', label: 'Medication Scheduler', icon: CalendarClock },
    { id: 'report', label: 'Doctor Prep Summary', icon: FileText },
    { id: 'records', label: 'Medical Index Logs', icon: FileSpreadsheet },
  ];

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId as TabType);
    setActiveRecordId(null); // clear record detail overlay
    setMobileMenuOpen(false);
  };

  const handleSelectRecord = (recordId: string) => {
    setActiveRecordId(recordId);
    setActiveTab('records'); // jump to logs tab to frame the details view
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col md:flex-row" id="app-root">
      
      {/* Mobile Top Header */}
      <div className="md:hidden bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold font-serif text-sm">
            AM
          </div>
          <span className="font-bold text-gray-800 font-serif text-sm">ArogyaMitra AI</span>
        </div>
        
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 text-gray-600 hover:text-teal-600 transition"
          id="btn-mobile-menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Persistent App Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-150 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:flex md:flex-col justify-between
        ${mobileMenuOpen ? 'translate-x-0 pt-14 md:pt-0' : '-translate-x-full'}
      `} id="app-sidebar">
        <div>
          {/* Brand/Logo */}
          <div className="hidden md:flex items-center gap-3 px-6 py-6 border-b border-gray-100">
            <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white font-bold font-serif shadow-sm">
              AM
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900 font-serif leading-none">ArogyaMitra AI</h1>
              <span className="text-[10px] font-bold text-teal-700 uppercase tracking-wider mt-1.5 block">Clinical Intelligence</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 py-6 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id && !activeRecordId;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabChange(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-bold transition-all ${
                    isActive 
                      ? 'bg-teal-50 text-teal-800 font-bold' 
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                  id={`nav-tab-${item.id}`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-teal-700' : 'text-gray-400'}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="px-6 py-4 border-t border-gray-100 space-y-4 bg-gray-50/50">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-800">
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            AES-256 Secured
          </div>
          <p className="text-[10px] text-gray-400 leading-relaxed">
            Your clinical data is symmetrical-encrypted and stored locally in compliance with strict privacy standards.
          </p>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-50 hover:bg-red-100 text-red-700 hover:text-red-800 text-[11px] font-bold rounded-lg transition-colors border border-red-100 shadow-sm"
            id="btn-sidebar-logout"
          >
            <LogOut className="w-3.5 h-3.5" />
            Clear Session & Logout
          </button>
        </div>
      </aside>

      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div 
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 bg-black/20 z-30 md:hidden"
        />
      )}

      {/* Main Panel Area */}
      <main className="flex-1 flex flex-col min-w-0">
        
        {/* Dynamic Nav-tab Header Bar (Desktop Only) */}
        <header className="hidden md:flex justify-between items-center bg-white border-b border-gray-100 px-8 py-4 sticky top-0 z-10 shadow-sm gap-4">
          <div className="flex items-center gap-6 flex-1 max-w-xl">
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider font-mono whitespace-nowrap shrink-0">
              {activeRecordId ? 'Record Details' : navItems.find(item => item.id === activeTab)?.label}
            </h2>
            
            {!activeRecordId && (
              <div className="relative w-full">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Quick find medical records by title or date (YYYY-MM-DD)..."
                  value={globalSearchTerm}
                  onChange={(e) => {
                    setGlobalSearchTerm(e.target.value);
                    if (activeTab !== 'records') {
                      setActiveTab('records');
                    }
                  }}
                  className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500 text-gray-800"
                  id="header-record-search"
                />
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-teal-700 shrink-0">
            <HeartHandshake className="w-4 h-4 text-teal-600" />
            Physician Collaboration Engine
          </div>
        </header>

        {/* Scrollable Stage Content */}
        <div className="flex-1 p-4 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto" id="stage-area">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeRecordId ? `detail-${activeRecordId}` : activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              {activeRecordId ? (
                /* Drill-down Record Details */
                <RecordDetailPage 
                  recordId={activeRecordId} 
                  onBack={() => setActiveRecordId(null)} 
                />
              ) : (
                /* Tab Panels */
                <>
                  {activeTab === 'dashboard' && (
                    <Dashboard 
                      onNavigate={handleTabChange} 
                      onSelectRecord={handleSelectRecord} 
                    />
                  )}
                  {activeTab === 'chat' && <AIChatbot />}
                  {activeTab === 'upload' && (
                    <UploadCenter 
                      onProcessingComplete={handleSelectRecord} 
                      onNavigate={handleTabChange} 
                    />
                  )}
                  {activeTab === 'timeline' && <TrendsTimeline />}
                  {activeTab === 'reminders' && <RemindersManager />}
                  {activeTab === 'report' && <DoctorPrep />}
                  {activeTab === 'records' && (
                    <RecordsLog 
                      onSelectRecord={handleSelectRecord} 
                      searchTerm={globalSearchTerm}
                      setSearchTerm={setGlobalSearchTerm}
                    />
                  )}
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

      </main>

    </div>
  );
}
