import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { documentService } from '../services/documentService';
import { emailService } from '../services/emailService';
import { progressService } from '../services/emailService';

const STEPS = ['Content', 'Styling', 'Recipients', 'Send'];
const FONTS = ['Helvetica', 'Times-Roman', 'Courier'];

export default function CreateDocument() {
  const [step, setStep] = useState(0);
  const [docData, setDocData] = useState({ name: '', content: '', font_size: 12, font_style: 'Helvetica', header: '', footer: '' });
  const [uploadedFile, setUploadedFile] = useState(null);
  const [inputMode, setInputMode] = useState('type'); // 'type' | 'upload'
  const [recipients, setRecipients] = useState([]);
  const [newRecipient, setNewRecipient] = useState({ name: '', email: '' });
  const [createdDoc, setCreatedDoc] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sendStarted, setSendStarted] = useState(false);
  const [progress, setProgress] = useState({ total: 0, sent: 0, failed: 0, in_progress: 0, pending: 0 });
  const [expiry, setExpiry] = useState({ hrs: 24, mins: 0, secs: 0 });
  const navigate = useNavigate();

  useEffect(() => { if (!authService.isAuthenticated()) navigate('/login'); }, []);

  const go = (n) => { setError(''); setStep(n); };
  const update = (field, val) => setDocData(p => ({ ...p, [field]: val }));

  // ── Step 1: Content ─────────────────────────────────────────────────────
  const handleFileSelect = (e) => setUploadedFile(e.target.files[0]);

  const validateStep0 = () => {
    if (!docData.name.trim()) { setError('Document name is required'); return false; }
    if (inputMode === 'type' && !docData.content.trim()) { setError('Please enter document content'); return false; }
    if (inputMode === 'upload' && !uploadedFile) { setError('Please upload a file'); return false; }
    return true;
  };

  // ── Step 3: Recipients ──────────────────────────────────────────────────
  const addRecipient = () => {
    if (!newRecipient.name.trim() || !newRecipient.email.trim()) { setError('Name and email required'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newRecipient.email)) { setError('Invalid email address'); return; }
    if (recipients.find(r => r.email === newRecipient.email)) { setError('Duplicate email'); return; }
    setError('');
    setRecipients(p => [...p, { ...newRecipient }]);
    setNewRecipient({ name: '', email: '' });
  };

  const removeRecipient = (email) => setRecipients(p => p.filter(r => r.email !== email));

  const handleBulkUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const parsed = await emailService.uploadRecipients(file);
      setRecipients(p => {
        const emails = new Set(p.map(r => r.email));
        return [...p, ...parsed.filter(r => !emails.has(r.email))];
      });
    } catch (err) { setError(typeof err === 'string' ? err : 'Could not parse file');
    } finally { setLoading(false); }
  };

  // ── Step 4: Create document + send ─────────────────────────────────────
  const handleCreateAndSend = async () => {
    if (recipients.length === 0) { setError('Add at least one recipient'); return; }
    setLoading(true); setError('');
    try {
      let doc;
      if (inputMode === 'upload' && uploadedFile) {
        const fd = new FormData();
        fd.append('name', docData.name); fd.append('font_size', docData.font_size);
        fd.append('font_style', docData.font_style); fd.append('header', docData.header || '');
        fd.append('footer', docData.footer || ''); fd.append('file', uploadedFile);
        doc = await documentService.uploadDocument(fd);
      } else {
        doc = await documentService.createDocument({ ...docData, recipients });
      }
      setCreatedDoc(doc);
      setCreatedDoc(doc);
      await emailService.sendEmails(doc.id, recipients, expiry);
      setSendStarted(true);
      // Poll progress
      const unsub = progressService.subscribeToProgress(doc.id,
        (data) => setProgress(data),
        () => setLoading(false),
        (err) => { setError(err); setLoading(false); }
      );
      return () => unsub();
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Failed to create or send document');
      setLoading(false);
    }
  };

  const pct = progress.total > 0 ? Math.round(((progress.sent + progress.failed) / progress.total) * 100) : 0;

  return (
    <div className="create-page page-enter">
      <div className="create-header">
        <button id="back-to-dashboard" className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <h1 style={{ fontSize: '1.3rem' }}>Create Secure Document</h1>
        <div />
      </div>

      {/* Step indicator */}
      <div className="step-indicator">
        {STEPS.map((label, i) => (
          <div key={label} className={`step${i === step ? ' active' : ''}${i < step ? ' done' : ''}`}>
            <div className="step-dot">{i < step ? '✓' : i + 1}</div>
            <span className="step-label">{label}</span>
          </div>
        ))}
      </div>

      <div className="create-body card">
        {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

        {/* ── STEP 0: Content ── */}
        {step === 0 && (
          <div className="step-content">
            <h3>Document Content</h3>
            <p className="step-desc">Enter content directly or upload a file (PDF, DOCX, TXT)</p>
            <div className="form-group" style={{ marginTop: 16 }}>
              <label className="form-label">Document Name *</label>
              <input className="form-input" placeholder="e.g. Q4 Strategy Report" value={docData.name} onChange={e => update('name', e.target.value)} />
            </div>
            <div className="mode-toggle">
              <button id="mode-type" className={`btn ${inputMode==='type'?'btn-primary':'btn-secondary'} btn-sm`} onClick={() => setInputMode('type')}>✏️ Type Content</button>
              <button id="mode-upload" className={`btn ${inputMode==='upload'?'btn-primary':'btn-secondary'} btn-sm`} onClick={() => setInputMode('upload')}>📄 Upload File</button>
            </div>
            {inputMode === 'type' ? (
              <div className="form-group" style={{ marginTop: 12 }}>
                <label className="form-label">Content</label>
                <textarea className="form-textarea" style={{ minHeight: 220 }} placeholder="Type your confidential document content here..." value={docData.content} onChange={e => update('content', e.target.value)} />
              </div>
            ) : (
              <label className="drop-zone" htmlFor="file-upload" style={{ display: 'block', marginTop: 12 }}>
                <div style={{ fontSize: 40, marginBottom: 8 }}>📎</div>
                <p style={{ fontWeight: 600 }}>{uploadedFile ? uploadedFile.name : 'Click to upload PDF, DOCX, or TXT'}</p>
                <p style={{ fontSize: 12, marginTop: 4 }}>Max file size: 10MB</p>
                <input id="file-upload" type="file" accept=".pdf,.docx,.txt" hidden onChange={handleFileSelect} />
              </label>
            )}
          </div>
        )}

        {/* ── STEP 1: Styling ── */}
        {step === 1 && (
          <div className="step-content">
            <h3>Document Styling</h3>
            <p className="step-desc">Customize how your document looks for all recipients</p>
            <div className="style-grid">
              <div className="form-group">
                <label className="form-label">Font Style</label>
                <select className="form-select" value={docData.font_style} onChange={e => update('font_style', e.target.value)}>
                  {FONTS.map(f => <option key={f}>{f}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Font Size</label>
                <input type="number" className="form-input" min={8} max={24} value={docData.font_size} onChange={e => update('font_size', Number(e.target.value))} />
              </div>
              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label className="form-label">Header (optional)</label>
                <input className="form-input" placeholder="e.g. CONFIDENTIAL — Acme Corp" value={docData.header} onChange={e => update('header', e.target.value)} />
              </div>
              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label className="form-label">Footer (optional)</label>
                <input className="form-input" placeholder="e.g. Page {page} — Internal Use Only" value={docData.footer} onChange={e => update('footer', e.target.value)} />
              </div>
            </div>
            <div className="doc-preview card" style={{ marginTop: 20 }}>
              <div style={{ fontFamily: docData.font_style === 'Helvetica' ? 'sans-serif' : docData.font_style === 'Courier' ? 'monospace' : 'serif', fontSize: docData.font_size, color: 'var(--text-primary)' }}>
                {docData.header && <div style={{ color: 'var(--text-muted)', fontSize: docData.font_size - 2, borderBottom: '1px solid var(--border)', paddingBottom: 8, marginBottom: 12 }}>{docData.header}</div>}
                <div style={{ opacity: 0.7, whiteSpace: 'pre-wrap', maxHeight: 100, overflow: 'hidden' }}>{docData.content || 'Your document content preview...'}</div>
                {docData.footer && <div style={{ color: 'var(--text-muted)', fontSize: docData.font_size - 3, borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 12 }}>{docData.footer}</div>}
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 2: Recipients ── */}
        {step === 2 && (
          <div className="step-content">
            <h3>Add Recipients</h3>
            <p className="step-desc">Each recipient gets a uniquely fingerprinted document</p>
            <div className="recipient-add-row">
              <input className="form-input" placeholder="Full name" value={newRecipient.name} onChange={e => setNewRecipient(p => ({ ...p, name: e.target.value }))} />
              <input className="form-input" type="email" placeholder="email@example.com" value={newRecipient.email} onChange={e => setNewRecipient(p => ({ ...p, email: e.target.value }))} onKeyDown={e => e.key === 'Enter' && addRecipient()} />
              <button id="add-recipient-btn" className="btn btn-primary" onClick={addRecipient}>+ Add</button>
            </div>
            <div style={{ textAlign: 'center', margin: '16px 0', color: 'var(--text-muted)', fontSize: 13 }}>— or —</div>
            <label className="btn btn-secondary" htmlFor="bulk-upload" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              📊 Upload CSV / Excel
              <input id="bulk-upload" type="file" accept=".csv,.xlsx,.xls" hidden onChange={handleBulkUpload} />
            </label>
            {recipients.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <p className="form-label" style={{ marginBottom: 10 }}>{recipients.length} recipient{recipients.length > 1 ? 's' : ''}</p>
                <div className="recipient-list">
                  {recipients.map(r => (
                    <div key={r.email} className="chip">
                      <span>👤 {r.name} &lt;{r.email}&gt;</span>
                      <span className="chip-remove" onClick={() => removeRecipient(r.email)}>×</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── STEP 3: Send ── */}
        {step === 3 && (
          <div className="step-content">
            <h3>Send Documents</h3>
            {!sendStarted ? (
              <>
                <p className="step-desc">Ready to fingerprint and send to {recipients.length} recipient{recipients.length !== 1 ? 's' : ''}. Each will receive a unique URL and password.</p>
                <div className="summary-grid" style={{ marginTop: 20 }}>
                  <div className="card"><p className="stat-label">Document</p><p style={{ fontWeight: 700, marginTop: 4 }}>{docData.name}</p></div>
                  <div className="card"><p className="stat-label">Recipients</p><p className="stat-number" style={{ fontSize: '1.5rem' }}>{recipients.length}</p></div>
                  <div className="card"><p className="stat-label">Font</p><p style={{ fontWeight: 700, marginTop: 4 }}>{docData.font_style} {docData.font_size}pt</p></div>
                </div>
                <button id="send-all-btn" className="btn btn-primary btn-lg" style={{ marginTop: 24, width: '100%' }}
                  onClick={handleCreateAndSend} disabled={loading}>
                  {loading ? <><span className="spinner" /> Creating...</> : '🚀 Fingerprint & Send All'}
                </button>

                <div className="expiry-setup card" style={{ marginTop: 24, padding: 16 }}>
                  <p className="form-label" style={{ marginBottom: 12 }}>🔒 Document Expiry Duration (Hrs:Min:Sec)</p>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: 10, color: 'var(--text-muted)' }}>Hours</label>
                      <input type="number" className="form-input" min={0} value={expiry.hrs} onChange={e => setExpiry(p => ({ ...p, hrs: parseInt(e.target.value) || 0 }))} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: 10, color: 'var(--text-muted)' }}>Minutes</label>
                      <input type="number" className="form-input" min={0} max={59} value={expiry.mins} onChange={e => setExpiry(p => ({ ...p, mins: parseInt(e.target.value) || 0 }))} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: 10, color: 'var(--text-muted)' }}>Seconds</label>
                      <input type="number" className="form-input" min={0} max={59} value={expiry.secs} onChange={e => setExpiry(p => ({ ...p, secs: parseInt(e.target.value) || 0 }))} />
                    </div>
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>Document will expire after this duration from the moment it is sent.</p>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <h3 style={{ marginBottom: 8, color: 'var(--accent)' }}>📤 Sending in Progress...</h3>
                <p style={{ marginBottom: 20, fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Processing: {progress.pending + progress.in_progress} recipient{progress.pending + progress.in_progress !== 1 ? 's' : ''} left
                </p>
                <div className="stat-grid" style={{ marginBottom: 16, gridTemplateColumns: 'repeat(3, 1fr)' }}>
                  <div className="stat-card"><div className="stat-number" style={{ color: 'var(--text-primary)' }}>{progress.total}</div><div className="stat-label">Total</div></div>
                  <div className="stat-card"><div className="stat-number" style={{ color: 'var(--success)' }}>{progress.sent}</div><div className="stat-label">Sent</div></div>
                  <div className="stat-card"><div className="stat-number" style={{ color: 'var(--danger)' }}>{progress.failed}</div><div className="stat-label">Failed</div></div>
                </div>

                <div className="processing-rectangle card" style={{ 
                  marginBottom: 24, 
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center', 
                  justifyContent: 'center',
                  padding: '20px 32px', 
                  background: 'rgba(99, 102, 241, 0.05)', 
                  border: '1px solid rgba(99, 102, 241, 0.2)', 
                  textAlign: 'center',
                  width: 'calc(100% + 40px)',
                  marginLeft: '-20px'
                }}>
                  <p style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 700, margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
                    System Processing
                  </p>
                  <p style={{ 
                    fontSize: 16, 
                    color: 'var(--text-primary)', 
                    margin: '8px 0 0 0', 
                    fontWeight: 500,
                    wordBreak: 'break-word',
                    overflowWrap: 'anywhere',
                    maxWidth: '100%',
                    lineHeight: '1.4'
                  }}>
                    {progress.current_action || 'Preparing system for next batch...'}
                  </p>
                </div>
                <div className="progress-bar-wrap" style={{ marginBottom: 16 }}>
                  <div className="progress-bar" style={{ width: `${pct}%` }} />
                </div>
                <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>{pct}% complete</p>
                {pct === 100 && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
                    <div className="success-tick" style={{ width: 64, height: 64, fontSize: 28 }} />
                    <p style={{ color: 'var(--success)', fontWeight: 700 }}>All emails processed!</p>
                    <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>View in Dashboard →</button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        {!sendStarted && (
          <div className="step-nav">
            {step > 0 && <button id="prev-step-btn" className="btn btn-secondary" onClick={() => go(step - 1)}>← Back</button>}
            {step < 3 && (
              <button id="next-step-btn" className="btn btn-primary" style={{ marginLeft: 'auto' }}
                onClick={() => { if (step === 0 && !validateStep0()) return; go(step + 1); }}>
                Next →
              </button>
            )}
          </div>
        )}
      </div>

      <style>{`
        .create-page { max-width: 760px; margin: 0 auto; padding: 24px; }
        .create-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }
        .create-body { padding: 32px; }
        .step-content { display: flex; flex-direction: column; gap: 8px; }
        .step-desc { color: var(--text-muted); font-size: 14px; margin-bottom: 4px; }
        .mode-toggle { display: flex; gap: 8px; margin-top: 12px; }
        .style-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
        .recipient-add-row { display: flex; gap: 10px; margin-top: 16px; }
        .recipient-add-row .form-input { flex: 1; }
        .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .step-nav { display: flex; margin-top: 28px; border-top: 1px solid var(--border); padding-top: 20px; }
        .doc-preview { padding: 16px; background: var(--bg-elevated); border: 1px dashed var(--border-light); }
      `}</style>
    </div>
  );
}
