import { useState, useEffect } from 'react';
import { trackingService } from '../services/trackingService';
import { documentService } from '../services/documentService';

const ACTION_ICON = {
  OPEN: '👁️', CLOSE: '🚪', COPY_ATTEMPT: '⛔', DOWNLOAD_ATTEMPT: '⛔',
};
const ACTION_COLOR = {
  OPEN: 'badge-success', CLOSE: 'badge-neutral',
  COPY_ATTEMPT: 'badge-danger', DOWNLOAD_ATTEMPT: 'badge-danger',
};

export default function ActivityLogs({ docId }) {
  const [logs, setLogs] = useState([]);
  const [docs, setDocs] = useState([]);
  const [selectedId, setSelectedId] = useState(docId || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDocs();
  }, []);

  useEffect(() => {
    if (docId) { setSelectedId(docId); loadLogs(docId); }
  }, [docId]);

  const loadDocs = async () => {
    try {
      const d = await documentService.listDocuments();
      setDocs(d);
      
      // Safety check: if the passed docId or selectedId is NOT in the new list, clear or reset it.
      // This prevents seeing "ghost" docs from previous login sessions.
      const exists = d.some(doc => doc.id === Number(selectedId));
      
      if (docId && !exists) {
        // The ID passed from Dashboard doesn't belong to current user
        setSelectedId('');
      } else if (!docId && d.length > 0 && !exists) {
        // Normal initialization: default to newest
        setSelectedId(d[0].id);
        loadLogs(d[0].id);
      }
    } catch { /* ignore */ }
  };

  const loadLogs = async (id) => {
    if (!id) return;
    setLoading(true); setError('');
    try {
      setLogs(await trackingService.getActivityLogs(id));
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Could not load activity logs');
    } finally { setLoading(false); }
  };

  const handleDocChange = (e) => {
    const id = Number(e.target.value);
    setSelectedId(id);
    loadLogs(id);
  };

  // Aggregate stats
  const totalOpens    = logs.filter(l => l.action === 'OPEN').length;
  const copyAttempts  = logs.filter(l => l.action === 'COPY_ATTEMPT').length;
  const dlAttempts    = logs.filter(l => l.action === 'DOWNLOAD_ATTEMPT').length;
  const uniqueEmails  = [...new Set(logs.map(l => l.receiver_email))].length;

  return (
    <div>
      {/* Document selector */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 20 }}>
        <div style={{ flex: 1 }}>
          <label className="form-label">Select Document</label>
          <select className="form-select" value={selectedId} onChange={handleDocChange}>
            <option value="">— choose a document —</option>
            {docs.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <button id="refresh-logs-btn" className="btn btn-secondary btn-sm" style={{ marginTop: 20 }} onClick={() => loadLogs(selectedId)} disabled={loading}>
          {loading ? <span className="spinner" /> : '↻ Refresh'}
        </button>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

      {/* Summary stats */}
      {logs.length > 0 && (
        <div className="stat-grid" style={{ marginBottom: 24 }}>
          <div className="stat-card"><div className="stat-number" style={{ color: 'var(--accent)' }}>{uniqueEmails}</div><div className="stat-label">Unique Recipients</div></div>
          <div className="stat-card"><div className="stat-number" style={{ color: 'var(--success)' }}>{totalOpens}</div><div className="stat-label">Total Opens</div></div>
          <div className="stat-card"><div className="stat-number" style={{ color: 'var(--danger)' }}>{copyAttempts}</div><div className="stat-label">Copy Attempts</div></div>
          <div className="stat-card"><div className="stat-number" style={{ color: 'var(--warning)' }}>{dlAttempts}</div><div className="stat-label">Download Attempts</div></div>
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 48 }} />)}
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>{selectedId ? 'No activity yet' : 'Select a document'}</h3>
          <p>{selectedId ? 'Activity will appear here once recipients open their documents' : 'Choose a document above to view its activity logs'}</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Recipient</th>
                <th>Action</th>
                <th>Timestamp</th>
                <th>Session</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id}>
                  <td style={{ fontSize: 13, fontFamily: 'monospace' }}>{log.receiver_email}</td>
                  <td>
                    <span className={`badge ${ACTION_COLOR[log.action] || 'badge-neutral'}`}>
                      {ACTION_ICON[log.action]} {log.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td style={{ fontSize: 13 }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={{ fontSize: 13 }}>{log.session_duration ? `${Math.round(log.session_duration)}s` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
