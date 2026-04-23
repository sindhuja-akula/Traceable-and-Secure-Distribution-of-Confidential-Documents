import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

export default function Login() {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [resetStep, setResetStep] = useState('none'); // 'none' | 'email' | 'otp' | 'password'
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  
  const [resetEmail, setResetEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPass, setNewPass] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (mode === 'register' && password !== confirmPass) {
      setError('Passwords do not match'); return;
    }
    setLoading(true);
    try {
      if (mode === 'login') {
        await authService.login(email, password);
        navigate('/dashboard');
      } else {
        await authService.register(email, password);
        setMode('login');
        setError('');
        alert('Account created! Please log in.');
      }
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Authentication failed');
    } finally { setLoading(false); }
  };

  // Password Reset Handlers
  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    const normalizedEmail = resetEmail.toLowerCase().trim();
    try {
      await authService.forgotPassword(normalizedEmail);
      setResetEmail(normalizedEmail);
      setResetStep('otp');
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      await authService.verifyOtp(resetEmail, otp);
      setResetStep('password');
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  const handleResetFinal = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setSuccess('');
    try {
      await authService.resetPassword(resetEmail, otp, newPass);
      setSuccess('Password updated successfully! You can now log in.');
      setResetStep('none');
      setMode('login');
      // Clear sensitive fields
      setOtp(''); setNewPass('');
    } catch (err) { setError(err); }
    finally { setLoading(false); }
  };

  return (
    <div className="login-page">
      <div className="login-bg-glow" />
      
      <div className="login-card page-enter">
        <div className="login-logo">
          <div className="logo-icon">🔒</div>
          <span className="logo-text">SecureDocs</span>
        </div>

        {success && <div className="alert alert-success" style={{ marginBottom: 20 }}>{success}</div>}

        {resetStep === 'none' ? (
          <>
            <h1 className="login-title">
              {mode === 'login' ? 'Welcome back' : 'Create account'}
            </h1>
            <p className="login-sub">
              {mode === 'login' ? 'Sign in to your secure workspace' : 'Start distributing documents securely'}
            </p>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <label className="form-label">Email</label>
                <input type="email" className="form-input" placeholder="you@company.com" 
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label className="form-label">Password</label>
                  {mode === 'login' && (
                    <button type="button" className="btn-link" style={{ fontSize: 12 }} 
                      onClick={() => setResetStep('email')}>Forgot Password?</button>
                  )}
                </div>
                <div className="password-input-wrapper">
                  <input type={showPassword ? "text" : "password"} className="form-input" placeholder="Min. 8 characters" 
                    value={password} onChange={e => setPassword(e.target.value)} required />
                  <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div className="form-group">
                  <label className="form-label">Confirm Password</label>
                  <input type={showPassword ? "text" : "password"} className="form-input" placeholder="Repeat password" 
                    value={confirmPass} onChange={e => setConfirmPass(e.target.value)} required />
                </div>
              )}

              <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
                {loading ? 'Processing...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
              </button>
            </form>

            <div className="login-switch">
              <p>{mode === 'login' ? "Don't have an account?" : "Already have an account?"}{' '}
                <button className="btn-link" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Sign up' : 'Sign in'}</button>
              </p>
            </div>
          </>
        ) : (
          <div className="reset-flow">
            <h1 className="login-title">Reset Password</h1>
            <p className="login-sub">
              {resetStep === 'email' && "Enter your email to receive a security code."}
              {resetStep === 'otp' && `We've sent a code to ${resetEmail}`}
              {resetStep === 'password' && "Verification successful! Enter your new password."}
            </p>

            {error && <div className="alert alert-error">{error}</div>}

            {resetStep === 'email' && (
              <form onSubmit={handleForgotSubmit} className="login-form">
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input type="email" className="form-input" placeholder="you@company.com" 
                    value={resetEmail} onChange={e => setResetEmail(e.target.value)} required autoFocus />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                  {loading ? 'Sending...' : 'Send OTP'}
                </button>
                <button type="button" className="btn btn-ghost" style={{ width: '100%' }} onClick={() => setResetStep('none')}>Back to Login</button>
              </form>
            )}

            {resetStep === 'otp' && (
              <form onSubmit={handleVerifyOtp} className="login-form">
                <div className="form-group">
                  <label className="form-label">6-Digit Code</label>
                  <input type="text" className="form-input" placeholder="000000" maxLength={6}
                    style={{ textAlign: 'center', fontSize: 24, letterSpacing: 8 }}
                    value={otp} onChange={e => setOtp(e.target.value)} required autoFocus />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                  {loading ? 'Verifying...' : 'Verify Code'}
                </button>
                <button type="button" className="btn btn-ghost" style={{ width: '100%' }} onClick={() => setResetStep('email')}>Resend Code</button>
              </form>
            )}

            {resetStep === 'password' && (
              <form onSubmit={handleResetFinal} className="login-form">
                <div className="form-group">
                  <label className="form-label">New Password</label>
                  <input type="password" className="form-input" placeholder="Min. 8 characters" 
                    value={newPass} onChange={e => setNewPass(e.target.value)} required autoFocus />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                  {loading ? 'Resetting...' : 'Update Password'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>

      <style>{`
        .login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; padding: 24px; }
        .login-bg-glow { position: absolute; width: 600px; height: 600px; background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%); top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none; }
        .login-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-xl); padding: 48px 40px; width: 100%; max-width: 420px; position: relative; z-index: 1; box-shadow: var(--shadow-md), 0 0 40px rgba(99,102,241,0.08); }
        .login-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 28px; }
        .logo-icon { font-size: 28px; }
        .logo-text { font-size: 20px; font-weight: 800; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .login-title { font-size: 1.6rem; font-weight: 800; margin-bottom: 6px; }
        .login-sub { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }
        .login-form { display: flex; flex-direction: column; gap: 16px; }
        .login-switch { text-align: center; margin-top: 20px; font-size: 14px; color: var(--text-muted); }
        .btn-link { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 14px; font-weight: 600; padding: 0; }
        .btn-link:hover { color: var(--accent-hover); text-decoration: underline; }
        .password-input-wrapper { position: relative; display: flex; align-items: center; }
        .password-toggle { position: absolute; right: 12px; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; padding: 4px; display: flex; align-items: center; justify-content: center; }
        .password-toggle:hover { color: var(--text-primary); }
        .reset-flow { animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
