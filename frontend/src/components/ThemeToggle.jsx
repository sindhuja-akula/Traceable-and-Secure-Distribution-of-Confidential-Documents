import React from 'react';

export default function ThemeToggle({ theme, toggleTheme }) {
  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle"
      aria-label="Toggle Theme"
    >
      <span className="theme-toggle-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
      <span className="theme-toggle-text">{theme === 'dark' ? 'Bright Mode' : 'Night Mode'}</span>
      <style>{`
        .theme-toggle {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          color: var(--text-primary);
          padding: 8px 16px;
          border-radius: 100px;
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          font-family: var(--font);
          font-size: 14px;
          font-weight: 600;
          transition: var(--transition);
          box-shadow: var(--shadow-sm);
          z-index: 1000;
          white-space: nowrap;
        }
        .theme-toggle:hover {
          transform: translateY(-1px);
          border-color: var(--accent);
          background: var(--bg-elevated);
          box-shadow: var(--shadow-md);
        }
        .theme-toggle-icon {
          font-size: 18px;
        }
      `}</style>
    </button>
  );
}
