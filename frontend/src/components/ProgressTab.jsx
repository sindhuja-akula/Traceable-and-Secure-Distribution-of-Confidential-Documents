import { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';
import { progressService } from '../services/emailService';

export default function ProgressTab({ onSelectDoc, selectedDocId }) {
  const [docs, setDocs] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const documents = await documentService.listDocuments();
      setDocs(documents);
      // Load progress for each
      const statMap = {};
      await Promise.all(documents.map(async (doc) => {
        try {
          statMap[doc.id] = await progressService.getProgress(doc.id);
        } catch { statMap[doc.id] = null; }
      }));
      setStats(statMap);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Could not load documents');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {[1,2,3].map(i => <div key={i} className="skeleton skeleton-card" />)}
    </div>
  );

  if (error) return <div className="alert alert-error">{error}</div>;

  if (docs.length === 0) return (
    <div className="empty-state">
      <div className="empty-state-icon">📊</div>
      <h3>No documents yet</h3>
      <p>Create a document to see sending progress here</p>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {docs.map(doc => {
        const s = stats[doc.id];
        const total = s?.total || 0;
        const sent = s?.sent || 0;
        const failed = s?.failed || 0;
        const pct = total > 0 ? Math.round(((sent + failed) / total) * 100) : 0;

        return (
          <div key={doc.id} className="card progress-doc-card"
            onClick={() => onSelectDoc?.(doc.id)}
            style={{ cursor: 'pointer', transition: 'var(--transition)' }}>
            <div className="section-header" style={{ marginBottom: 12 }}>
              <div>
                <h4 style={{ marginBottom: 2 }}>{doc.name}</h4>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Created {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {s && <>
                  <span className="badge badge-success">{sent} sent</span>
                  {failed > 0 && <span className="badge badge-danger">{failed} failed</span>}
                  {(s.pending + s.in_progress) > 0 && <span className="badge badge-warning">{s.pending + s.in_progress} pending</span>}
                </>}
              </div>
            </div>
            {s && total > 0 ? (
              <>
                <div className="progress-bar-wrap">
                  <div className="progress-bar" style={{ width: `${pct}%` }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                  <span>{pct}% complete</span>
                  <span>{total} total recipients</span>
                </div>
              </>
            ) : (
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No emails sent yet</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
