import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/authService';
import ProgressTab from '../components/ProgressTab';
import HistoryTab from '../components/HistoryTab';
import ActivityLogs from '../components/ActivityLogs';
import LeakDetection from './LeakDetection';

const TABS = ['Progress', 'History', 'Activity Logs', 'Leak Detection'];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('History');
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authService.isAuthenticated()) { navigate('/login'); return; }
    const currUser = authService.getCurrentUser();
    setUser(currUser);
    
    // Reset selection if user changed (safety for multi-account toggling)
    setSelectedDocId(null);
    setActiveTab('History');
  }, [navigate]);

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🔒</span>
          <span className="logo-text">SecureDocs</span>
        </div>

        <nav className="sidebar-nav">
          {TABS.map(tab => (
            <button key={tab} id={`tab-${tab.replace(/\s+/g,'-').toLowerCase()}`}
              className={`sidebar-item${activeTab === tab ? ' active' : ''}`}
              onClick={() => setActiveTab(tab)}>
              <span>{tab === 'Progress' ? '📊' : tab === 'History' ? '📁' : tab === 'Activity Logs' ? '📋' : '🕵️'}</span>
              {tab}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <Link to="/create" className="btn btn-primary" id="create-doc-btn" style={{ width: '100%', justifyContent: 'center' }}>
            + New Document
          </Link>
          <div className="user-pill">
            <div className="user-avatar">{user?.email?.[0]?.toUpperCase() || '?'}</div>
            <div className="user-info">
              <span className="user-email">{user?.email}</span>
              <button id="logout-btn" className="btn-link text-danger" onClick={handleLogout}>Logout</button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="dashboard-main page-enter">
        <div className="dashboard-header">
          <div>
            <h1 style={{ fontSize: '1.4rem' }}>
              {activeTab === 'Progress' && '📊 Sending Progress'}
              {activeTab === 'History' && '📁 Document History'}
              {activeTab === 'Activity Logs' && '📋 Activity Logs'}
              {activeTab === 'Leak Detection' && '🕵️ Comprehensive Leak Scan'}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>
              {activeTab === 'History' && 'All documents you\'ve created and distributed'}
              {activeTab === 'Progress' && 'Live status of email sending jobs'}
              {activeTab === 'Activity Logs' && 'Detailed per-recipient behaviour logs'}
              {activeTab === 'Leak Detection' && 'Scan a leaked document to identify the specific person responsible'}
            </p>
          </div>
        </div>

        <div className="dashboard-content">
          {activeTab === 'Progress'      && <ProgressTab onSelectDoc={setSelectedDocId} selectedDocId={selectedDocId} />}
          {activeTab === 'History'       && <HistoryTab onSelectDoc={(id) => { setSelectedDocId(id); setActiveTab('Activity Logs'); }} />}
          {activeTab === 'Activity Logs' && <ActivityLogs docId={selectedDocId} />}
          {activeTab === 'Leak Detection' && <LeakDetection />}
        </div>
      </main>

    </div>
  );
}
