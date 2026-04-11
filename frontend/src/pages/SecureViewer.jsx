import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { trackingService } from '../services/trackingService';

export default function SecureViewer() {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [warning, setWarning] = useState('');
  const [warningCount, setWarningCount] = useState(0);
  const [blocked, setBlocked] = useState(false);
  const openedAt = useRef(Date.now());
  const warningTimer = useRef(null);

  // Clear warning after 3 seconds
  const showWarning = useCallback(async (msg) => {
    setWarning(msg);
    if (warningTimer.current) clearTimeout(warningTimer.current);
    warningTimer.current = setTimeout(() => setWarning(''), 3000);
    // Track + warn on server
    try {
      const result = await trackingService.recordWarning(token);
      setWarningCount(result.warning_count || 0);
      if (result.blocked) setBlocked(true);
    } catch { /* non-fatal */ }
  }, [token]);

  // Security: disable copy, right-click, download
  useEffect(() => {
    if (!authenticated) return;
    const noop = (e) => { e.preventDefault(); e.stopPropagation(); showWarning('⚠️ Copying is not allowed for this document'); };
    const noRightClick = (e) => { e.preventDefault(); showWarning('⚠️ Right-click is disabled for this document'); };
    document.addEventListener('copy', noop);
    document.addEventListener('cut', noop);
    document.addEventListener('contextmenu', noRightClick);
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && ['c','x','s','p','a'].includes(e.key.toLowerCase())) {
        e.preventDefault();
        showWarning(`⚠️ Keyboard shortcut Ctrl+${e.key.toUpperCase()} is disabled`);
      }
    });
    return () => {
      document.removeEventListener('copy', noop);
      document.removeEventListener('cut', noop);
      document.removeEventListener('contextmenu', noRightClick);
    };
  }, [authenticated, showWarning]);

  // Log close / session duration on unmount
  useEffect(() => {
    return () => {
      if (authenticated && token) {
        const duration = (Date.now() - openedAt.current) / 1000;
        trackingService.trackAction(token, 'CLOSE', duration);
      }
    };
  }, [authenticated, token]);

  const handleAccess = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const result = await trackingService.accessDocument(token, password);
      setDoc(result);
      setAuthenticated(true);
      openedAt.current = Date.now();
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Access denied');
    } finally {
      setLoading(false);
    }
  };

  if (blocked) return (
    <div className="blocked-overlay">
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>🚫</div>
        <h2 style={{ color: 'var(--danger)', marginBottom: 8 }}>Access Blocked</h2>
        <p style={{ color: 'var(--text-muted)' }}>This link has been blocked due to repeated security violations.</p>
      </div>
    </div>
  );

  if (!authenticated) return (
    <div className="viewer-gate">
      <div className="viewer-gate-card page-enter">
        <div style={{ fontSize: 48, marginBottom: 16, textAlign: 'center' }}>🔒</div>
        <h2 style={{ textAlign: 'center', marginBottom: 6 }}>Secure Document</h2>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: 14, marginBottom: 24 }}>Enter your password to access this document</p>
        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}
        <form onSubmit={handleAccess} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">Access Password</label>
            <input id="doc-password-input" type="password" className="form-input" placeholder="Enter password from email" value={password} onChange={e => setPassword(e.target.value)} autoFocus required />
          </div>
          <button id="access-doc-btn" type="submit" className="btn btn-primary btn-lg" disabled={loading}>
            {loading ? <><span className="spinner" /> Verifying...</> : 'Access Document →'}
          </button>
        </form>
      </div>
      <style>{`
        .viewer-gate { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }
        .viewer-gate-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-xl); padding: 40px; width: 100%; max-width: 380px; }
      `}</style>
    </div>
  );

  return (
    <div className="viewer-page"
      onDragStart={e => { e.preventDefault(); showWarning('⚠️ Dragging is not allowed'); }}
      style={{ userSelect: 'none', WebkitUserSelect: 'none' }}>

      {/* Warning banner */}
      {warning && <div className={`warning-banner shake`}>{warning}{warningCount >= 3 && ` (${warningCount}/5)`}</div>}

      {/* Header bar */}
      <div className="viewer-topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>🔒</span>
          <span style={{ fontWeight: 700 }}>{doc.document_name}</span>
          <span className="badge badge-warning" style={{ marginLeft: 8 }}>CONFIDENTIAL</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            {doc.receiver_email}
          </span>
          {doc.expires_at && (
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              Expires: {new Date(doc.expires_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Document content */}
      <div className="viewer-body">
        <div className="viewer-doc"
          onCopy={e => { e.preventDefault(); showWarning('⚠️ Copying is not allowed'); }}
          onCut={e => { e.preventDefault(); showWarning('⚠️ Cutting is not allowed'); }}>
          
          {/* Watermark Overlay */}
          <div className="watermark-overlay"></div>
          
          {doc.header && <div className="doc-header">{doc.header}</div>}
          <div className="doc-body" style={{ fontFamily: doc.font_style === 'Courier' ? 'monospace' : doc.font_style === 'Times-Roman' ? 'serif' : 'sans-serif', fontSize: doc.font_size }}>
            {doc.content.split('\n\n').map((para, i) => <p key={i} style={{ marginBottom: '1em' }}>{para}</p>)}
          </div>
          {doc.footer && <div className="doc-footer">{doc.footer}</div>}
        </div>
      </div>

      <style>{`
        .viewer-page { min-height: 100vh; display: flex; flex-direction: column; }
        .viewer-topbar {
          background: var(--bg-surface); border-bottom: 1px solid var(--border);
          padding: 14px 32px; display: flex; align-items: center; justify-content: space-between;
          position: sticky; top: 0; z-index: 100;
        }
        .viewer-body { flex: 1; padding: 40px; max-width: 800px; margin: 0 auto; width: 100%; }
        .viewer-doc { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 48px; position: relative; }
        .watermark-overlay {
          position: absolute; top: 0; left: 0; width: 100%; height: 100%;
          pointer-events: none; z-index: 1;
          opacity: 0.1; 
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E%3Ctext x='0' y='100' font-size='16' font-family='sans-serif' font-weight='700' fill='%236366f1' transform='rotate(-35, 150, 100)'%3E${encodeURIComponent(doc.receiver_email)}%3C/text%3E%3C/svg%3E");
          background-repeat: repeat;
        }
        .doc-header { color: var(--text-muted); font-size: 13px; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 24px; text-align: center; position: relative; z-index: 2; }
        .doc-body { line-height: 1.8; color: var(--text-primary); position: relative; z-index: 2; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; white-space: pre-wrap; }
        .doc-footer { color: var(--text-muted); font-size: 12px; border-top: 1px solid var(--border); padding-top: 12px; margin-top: 24px; text-align: center; position: relative; z-index: 2; }
      `}</style>
    </div>
  );
}
