import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { documentService } from '../services/documentService';
import { emailService } from '../services/emailService';

export default function HistoryTab({ onSelectDoc }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedDoc, setExpandedDoc] = useState(null);
  const [logs, setLogs] = useState({});
  
  // Selection Mode State
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [confirmingDoc, setConfirmingDoc] = useState(null);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const [isBulkConfirming, setIsBulkConfirming] = useState(false);

  // Drag-to-Select State
  const [isDragging, setIsDragging] = useState(false);

  // Long Press Refs
  const pressTimerRef = useRef(null);
  const isLongPressApplied = useRef(false);

  const navigate = useNavigate();

  // Add global mouseup listener to stop dragging
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      setIsDragging(false);
      if (pressTimerRef.current) {
        clearTimeout(pressTimerRef.current);
        pressTimerRef.current = null;
      }
    };
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, []);

  useEffect(() => { loadDocs(); }, []);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const data = await documentService.listDocuments();
      setDocs(data);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Could not load documents');
    } finally { setLoading(false); }
  };

  const toggleExpand = async (doc) => {
    if (expandedDoc === doc.id) { setExpandedDoc(null); return; }
    setExpandedDoc(doc.id);
    if (!logs[doc.id]) {
      try {
        const logData = await emailService.getEmailLogs(doc.id);
        setLogs(p => ({ ...p, [doc.id]: logData }));
      } catch { setLogs(p => ({ ...p, [doc.id]: [] })); }
    }
  };

  // Selection Handlers
  const enterSelectionMode = (docId) => {
    setIsSelectionMode(true);
    setIsDragging(true);
    if (!selectedIds.includes(docId)) {
      setSelectedIds(prev => [...prev, docId]);
    }
    if (window.navigator?.vibrate) window.navigator.vibrate(50);
  };

  const exitSelectionMode = () => {
    setIsSelectionMode(false);
    setSelectedIds([]);
    setIsBulkConfirming(false);
    setIsDragging(false);
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === docs.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(docs.map(d => d.id));
    }
  };

  // Drag-Selection Logic
  const handleMouseEnter = (docId) => {
    if (isSelectionMode && isDragging) {
      if (!selectedIds.includes(docId)) {
        setSelectedIds(prev => [...prev, docId]);
      }
    }
  };

  // Click vs Long Press Logic
  const handlePressStart = (docId) => {
    isLongPressApplied.current = false;
    // If already in selection mode, start dragging immediately
    if (isSelectionMode) {
      setIsDragging(true);
      if (!selectedIds.includes(docId)) setSelectedIds(prev => [...prev, docId]);
      return;
    }

    pressTimerRef.current = setTimeout(() => {
      isLongPressApplied.current = true;
      enterSelectionMode(docId);
    }, 600); // 600ms threshold
  };

  const handlePressEnd = (doc, e) => {
    if (pressTimerRef.current) {
      clearTimeout(pressTimerRef.current);
      pressTimerRef.current = null;
    }

    // If it was NOT a long press, do the normal click action
    if (!isLongPressApplied.current) {
      if (isSelectionMode) {
        // Just toggle individual selection if it was a quick click in selection mode
        if (!isDragging) toggleSelect(doc.id);
      } else {
        toggleExpand(doc);
      }
    }
    setIsDragging(false);
  };

  // Delete Handlers
  const handleDeleteSingle = async (docId) => {
    try {
      await documentService.deleteDocument(docId);
      setDocs(prev => prev.filter(d => d.id !== docId));
      setSelectedIds(prev => prev.filter(i => i !== docId));
      setConfirmingDoc(null);
      if (docs.length <= 1) exitSelectionMode(); // Exit if last doc deleted
    } catch (err) {
      alert(err);
    }
  };

  const handleDeleteBulk = async () => {
    setIsBulkDeleting(true);
    try {
      await documentService.bulkDeleteDocuments(selectedIds);
      setDocs(prev => prev.filter(d => !selectedIds.includes(d.id)));
      exitSelectionMode();
    } catch (err) {
      alert(err);
    } finally {
      setIsBulkDeleting(false);
    }
  };

  const statusColor = (s) => ({ SENT: 'badge-success', FAILED: 'badge-danger', PENDING: 'badge-neutral', IN_PROGRESS: 'badge-warning' }[s] || 'badge-neutral');

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 72 }} />)}
    </div>
  );

  if (error) return <div className="alert alert-error">{error}</div>;
  
  if (docs.length === 0) return (
    <div className="empty-state">
      <div className="empty-state-icon">📁</div>
      <h3>No documents yet</h3>
      <p>Your created documents will appear here</p>
      <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/create')}>+ Create First Document</button>
    </div>
  );

  return (
    <div className="history-tab">
      {/* Header with Selection Info */}
      <div className="section-header" style={{ marginBottom: 20 }}>
        {isSelectionMode ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <input 
              type="checkbox" 
              className="checkbox-custom"
              checked={docs.length > 0 && selectedIds.length === docs.length}
              onChange={toggleSelectAll}
            />
            <span className="section-title" style={{ color: 'var(--accent)' }}>
              {selectedIds.length} Selected
            </span>
            <button className="btn btn-ghost btn-sm" onClick={exitSelectionMode}>✖ Cancel</button>
          </div>
        ) : (
          <div>
            <span className="section-title">{docs.length} Document{docs.length !== 1 ? 's' : ''}</span>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              💡 <b>Double click and hold</b> or <b>double click and drag</b> to select multiple documents.
            </p>
          </div>
        )}
        
        <div style={{ display: 'flex', gap: 10 }}>
          {isSelectionMode && selectedIds.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {!isBulkConfirming ? (
                <button className="btn btn-danger btn-sm" onClick={() => setIsBulkConfirming(true)}>
                  🗑️ Delete Selected
                </button>
              ) : (
                <div className="bulk-confirm-inline">
                  <span style={{ fontSize: 12, marginRight: 8 }}>Delete {selectedIds.length}?</span>
                  <button className="btn btn-danger btn-sm" onClick={handleDeleteBulk} disabled={isBulkDeleting}>
                    {isBulkDeleting ? 'Deleting...' : 'Yes'}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setIsBulkConfirming(false)}>No</button>
                </div>
              )}
            </div>
          )}
          {!isSelectionMode && <button id="new-doc-btn" className="btn btn-primary btn-sm" onClick={() => navigate('/create')}>+ New Document</button>}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {docs.map(doc => (
          <div key={doc.id} style={{ position: 'relative' }}>
            <div 
              className={`card history-doc-row ${selectedIds.includes(doc.id) ? 'selected' : ''} ${isSelectionMode ? 'selection-active' : ''}`} 
              onMouseDown={() => handlePressStart(doc.id)}
              onMouseUp={(e) => handlePressEnd(doc, e)}
              onMouseEnter={() => handleMouseEnter(doc.id)}
              onTouchStart={() => handlePressStart(doc.id)}
              onTouchEnd={(e) => handlePressEnd(doc, e)}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  {isSelectionMode && (
                    <input 
                      type="checkbox" 
                      className="checkbox-custom"
                      checked={selectedIds.includes(doc.id)}
                      readOnly
                    />
                  )}
                  <div className="doc-icon">📄</div>
                  <div>
                    <p style={{ fontWeight: 600, marginBottom: 2 }}>{doc.name}</p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {new Date(doc.created_at).toLocaleString()} · {doc.font_style} {doc.font_size}pt
                    </p>
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }} onClick={e => e.stopPropagation()}>
                  {!isSelectionMode && (!confirmingDoc || confirmingDoc !== doc.id ? (
                    <>
                      <button className="btn btn-ghost btn-sm" onClick={() => onSelectDoc?.(doc.id)}>View Logs</button>
                      <button 
                        className="btn btn-ghost btn-sm delete-btn" 
                        onClick={() => setConfirmingDoc(doc.id)}
                        title="Delete Document"
                      >
                        🗑️ Delete
                      </button>
                    </>
                  ) : (
                    <div className="delete-confirm-overlay">
                      <span style={{ fontSize: 12, marginRight: 8 }}>Sure?</span>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDeleteSingle(doc.id)}>Yes</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => setConfirmingDoc(null)}>No</button>
                    </div>
                  ))}
                  <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>{expandedDoc === doc.id ? '▲' : '▼'}</span>
                </div>
              </div>

              {expandedDoc === doc.id && !isSelectionMode && (
                <div className="doc-logs-expanded">
                  <p className="logs-header">Email Logs</p>
                  {!logs[doc.id] ? (
                    <div className="skeleton" style={{ height: 40 }} />
                  ) : logs[doc.id].length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>No emails sent yet</p>
                  ) : (
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Recipient</th>
                            <th>Status</th>
                            <th>Opened</th>
                            <th>Expires</th>
                            <th>Blocked</th>
                          </tr>
                        </thead>
                        <tbody>
                          {logs[doc.id].map(log => (
                            <tr key={log.id}>
                              <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{log.receiver_email}</td>
                              <td><span className={`badge ${statusColor(log.status)}`}>{log.status}</span></td>
                              <td style={{ fontSize: 13 }}>{log.opened_at ? new Date(log.opened_at).toLocaleString() : '—'}</td>
                              <td style={{ fontSize: 13 }}>{log.expires_at ? new Date(log.expires_at).toLocaleString() : '—'}</td>
                              <td>{log.is_blocked ? <span className="badge badge-danger">Blocked</span> : <span className="badge badge-success">Active</span>}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
