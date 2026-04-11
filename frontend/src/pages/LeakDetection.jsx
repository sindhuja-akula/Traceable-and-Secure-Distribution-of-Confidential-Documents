import { useState } from 'react';
import { trackingService } from '../services/trackingService';

export default function LeakDetection() {
  const [scanMode, setScanMode] = useState('file'); // 'file' or 'url'
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDetect = async (e) => {
    e.preventDefault();
    if (scanMode === 'file' && !file) { setError('Please select a file to scan'); return; }
    if (scanMode === 'url' && !url) { setError('Please paste a leak URL to scan'); return; }
    
    setLoading(true); setError(''); setResult(null);
    try {
      let res;
      if (scanMode === 'file') {
        res = await trackingService.analyzeDocument(file);
      } else {
        res = await trackingService.analyzeUrl(url);
      }
      setResult(res);
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Leak detection failed');
    } finally {
      setLoading(false);
    }
  };

  const renderResultSection = (title, data, icon) => {
    if (!data) return null;
    return (
      <div className={`analysis-section ${data.identified ? 'identified' : 'clean'}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 20 }}>{icon}</span>
          <h3 style={{ margin: 0, fontSize: 16 }}>{title}</h3>
        </div>
        
        {data.identified ? (
          <div>
            <div 
              className="status-badge" 
              style={{ 
                display: 'inline-block', 
                marginBottom: 12,
                background: data.confidence_score >= 80 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: data.confidence_score >= 80 ? 'var(--danger-color)' : '#f59e0b'
              }}
            >
              {data.confidence_score >= 80 ? '🚨 HIGH CONFIDENCE MATCH' : '⚠️ MODERATE MATCH'}
            </div>
            <table style={{ width: '100%', fontSize: 14 }}>
              <tbody>
                <tr><td style={{ color: 'var(--text-muted)', padding: '4px 0', paddingRight: 16 }}>Identified Person</td><td style={{ fontWeight: 700, color: data.confidence_score >= 80 ? 'var(--danger-color)' : '#f59e0b' }}>{data.leaker_email}</td></tr>
                {(data.confidence_score || data.match_ratio) && (
                  <tr>
                    <td style={{ color: 'var(--text-muted)', padding: '4px 0' }}>Match Confidence</td>
                    <td style={{ fontWeight: 600 }}>{data.confidence_score ? data.confidence_score.toFixed(1) : (data.match_ratio * 100).toFixed(1)}%</td>
                  </tr>
                )}
                {data.trace_id && <tr><td style={{ color: 'var(--text-muted)', padding: '4px 0' }}>Trace ID</td><td style={{ fontFamily: 'monospace', fontSize: 12 }}>{data.trace_id}</td></tr>}
              </tbody>
            </table>
            <p style={{ fontSize: 13, marginTop: 8, color: 'var(--text-muted)', lineHeight: 1.4 }}>{data.message}</p>
          </div>
        ) : (
          <div>
            <div className="status-badge success" style={{ display: 'inline-block', marginBottom: 12 }}>✅ NO MATCH</div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{data.message}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="leak-page page-enter">
      <div className="leak-card card">
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 48, marginBottom: 10 }}>🔍</div>
          <h2>Comprehensive Leak Hub</h2>
          
          {/* Instructions Note */}
          <div className="info-note" style={{ 
            marginTop: 16, 
            padding: '12px 16px', 
            background: 'var(--bg-secondary)', 
            borderRadius: 8, 
            fontSize: 13, 
            color: 'var(--text-muted)',
            border: '1px solid var(--border-color)',
            lineHeight: 1.5
          }}>
            👋 <b>How to scan:</b> Upload <b>URLs, Screenshots, PDFs, or .txt files</b> to identify the recipient of a leaked document instantly.
          </div>
        </div>

        {/* Clear Scan Mode Toggle */}
        <div className="scan-toggle" style={{ 
          display: 'flex', 
          background: 'var(--bg-secondary)', 
          padding: 4, 
          borderRadius: 10, 
          marginBottom: 24,
          border: '1px solid var(--border-color)'
        }}>
          <button 
            className={`toggle-btn ${scanMode === 'file' ? 'active' : ''}`}
            onClick={() => { setScanMode('file'); setResult(null); setError(''); }}
          >
            📸 Document / Screenshot
          </button>
          <button 
            className={`toggle-btn ${scanMode === 'url' ? 'active' : ''}`}
            onClick={() => { setScanMode('url'); setResult(null); setError(''); }}
          >
            🔗 Leak URL / Link
          </button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

        <form onSubmit={handleDetect} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {scanMode === 'file' ? (
            <label className="drop-zone" htmlFor="leak-file">
              <div style={{ fontSize: 44, marginBottom: 12 }}>📥</div>
              <p style={{ fontWeight: 700, fontSize: 16 }}>{file ? file.name : 'Select or drop PDF, Image, or Doc'}</p>
              <p style={{ fontSize: 13, marginTop: 8, color: 'var(--text-muted)', maxWidth: 400 }}>
                We use AI-powered OCR to read screenshots and diagonal watermarks
              </p>
              <input id="leak-file" type="file" accept=".pdf,.png,.jpg,.jpeg,.txt,.docx" hidden onChange={e => setFile(e.target.files[0])} />
            </label>
          ) : (
            <div className="url-input-container">
              <input 
                type="text" 
                className="input input-lg" 
                placeholder="Paste the leaked viewing URL here (e.g. http://.../view/abc123...)"
                value={url}
                onChange={e => setUrl(e.target.value)}
                style={{ width: '100%', marginBottom: 8 }}
              />
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
                Paste the specific private link sent to a recipient for a 100% accurate match.
              </p>
            </div>
          )}

          <button id="detect-leak-btn" type="submit" className="btn btn-primary btn-lg" disabled={loading || (scanMode === 'file' ? !file : !url)}>
            {loading ? <><span className="spinner" /> Analyzing...</> : `🎯 Start ${scanMode === 'file' ? 'Multi-Base Scan' : 'Instant URL Match'}`}
          </button>
        </form>

        {result && (
          <div style={{ marginTop: 32, display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 12, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>Analysis Results</h3>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {scanMode === 'file' ? 'Comprehensive Scan Complete' : 'Direct URL Identity Verification'}
              </span>
            </div>
            
            {renderResultSection("Visible Watermark Analysis", result.watermark_analysis, "👁️")}
            {renderResultSection("Hidden Trace ID Analysis", result.trace_id_analysis, "🕵️")}
            {renderResultSection("Semantic Phrasing Analysis", result.phrasing_analysis, "🧠")}

            {/* Diagnostic Text Preview & Quota Alerts */}
            {scanMode === 'file' && (
              <div style={{ 
                marginTop: 24, 
                padding: 20, 
                background: 'var(--bg-secondary)', 
                borderRadius: 'var(--radius-md)', 
                border: (result.extracted_text_preview?.includes("GOOGLE API ERROR") || result.extracted_text_preview?.includes("429") || result.extracted_text_preview?.includes("Quota")) 
                  ? '1px solid var(--danger-color)' 
                  : '1px dashed var(--border-color)' 
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <span style={{ fontSize: 16 }}>{(result.extracted_text_preview?.includes("GOOGLE API ERROR") || result.extracted_text_preview?.includes("429") || result.extracted_text_preview?.includes("Quota")) ? '⚠️' : '📝'}</span>
                  <h4 style={{ margin: 0, fontSize: 14 }}>
                    {(result.extracted_text_preview?.includes("GOOGLE API ERROR") || result.extracted_text_preview?.includes("429") || result.extracted_text_preview?.includes("Quota")) 
                      ? 'CRITICAL API ERROR DETECTED' 
                      : 'Extracted Text Preview (AI View)'}
                  </h4>
                </div>

                {(result.extracted_text_preview?.includes("GOOGLE API ERROR") || result.extracted_text_preview?.includes("429") || result.extracted_text_preview?.includes("Quota")) && (
                  <div style={{ 
                    background: 'rgba(239, 68, 68, 0.1)', 
                    padding: 12, 
                    borderRadius: 6, 
                    marginBottom: 16, 
                    fontSize: 13, 
                    color: 'var(--danger-color)', 
                    lineHeight: 1.5,
                    border: '1px solid rgba(239, 68, 68, 0.2)'
                  }}>
                    <strong>The Google Gemini API is rejecting your requests.</strong><br/>
                    Model: Gemini 2.5 Stable Fallback<br/>
                    Reason: {result.extracted_text_preview}<br/><br/>
                    <strong>How to Fix:</strong><br/>
                    1. Verify that "Gemini 2.5 Flash" is enabled in your <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" style={{ color: 'inherit', fontWeight: 'bold' }}>Google AI Studio</a> project.<br/>
                    2. Even for free tier, Google often requires a linked Billing Account (Credit Card) for Vision/OCR quotas to be active. 
                  </div>
                )}

                <div style={{ 
                  fontFamily: 'monospace', 
                  fontSize: 11, 
                  color: (result.extracted_text_preview?.includes("429") || result.extracted_text_preview?.includes("Quota")) ? 'var(--danger-color)' : 'var(--text-muted)', 
                  maxHeight: 120, 
                  overflowY: 'auto', 
                  background: 'rgba(255,255,255,0.02)', 
                  padding: 12, 
                  borderRadius: 4,
                  lineHeight: 1.6,
                  border: '1px solid rgba(255,255,255,0.05)'
                }}>
                  {result.extracted_text_preview || "No text could be extracted."}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        .leak-page { max-width: 600px; margin: 0 auto; padding: 40px 24px; }
        .leak-card { padding: 40px; }
        .analysis-section { border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; transition: all 0.2s; }
        .analysis-section.identified { border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.05); }
        .analysis-section.clean { border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.05); }
        .status-badge { font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 12px; letter-spacing: 0.05em; }
        .status-badge.error { background: rgba(239, 68, 68, 0.2); color: var(--danger-color); }
        .status-badge.success { background: rgba(34, 197, 94, 0.2); color: var(--success-color); }
        
        .scan-toggle .toggle-btn {
          flex: 1;
          padding: 10px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.2s;
        }
        
        .scan-toggle .toggle-btn.active {
          background: var(--bg-primary);
          color: var(--text-color);
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .url-input-container .input {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          padding: 16px;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}
