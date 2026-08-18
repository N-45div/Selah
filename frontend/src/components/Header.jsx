import React, { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Radio, ShieldCheck, Tv, FileText, ExternalLink, Moon, Sun, Monitor } from 'lucide-react';

export default function Header({ currentPlan, streamStatus }) {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const isLive = streamStatus === 'live' || (currentPlan && currentPlan.status === 'live');
  const isEnded = streamStatus === 'ended' || (currentPlan && currentPlan.status === 'ended');

  // Toggle Dark Studio Mode
  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const nextVal = !prev;
      if (nextVal) {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
      return nextVal;
    });
  };

  return (
    <header className="app-header">
      <Link to="/" className="logo-area">
        <span className="brand-icon">🕊️</span>
        <div>
          <h1 className="brand-title">Selah</h1>
          <p className="brand-tagline">Live Telecast Copilot for Church Media</p>
        </div>
      </Link>

      <nav className="header-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <ShieldCheck size={17} />
          <span>1. Prepare & License</span>
        </NavLink>

        <NavLink to="/console" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Radio size={17} />
          <span>2. Live Console</span>
        </NavLink>

        <NavLink to="/closeout" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileText size={17} />
          <span>3. Close-Out & Pack</span>
        </NavLink>

        <a 
          href="/output" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
          title="Open OBS / vMix Output Window"
        >
          <Tv size={17} />
          <span>OBS Output</span>
          <ExternalLink size={13} style={{ opacity: 0.7 }} />
        </a>

        <a 
          href="/stage" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
          title="Open Stage Confidence Monitor"
        >
          <Monitor size={17} color="var(--amber-accent)" />
          <span>Stage Monitor</span>
          <ExternalLink size={13} style={{ opacity: 0.7 }} />
        </a>
      </nav>

      <div className="header-status">
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title="Toggle Studio Dark Booth Mode"
        >
          {isDarkMode ? <><Sun size={14} color="#f0c56e" /> Paper</> : <><Moon size={14} /> Studio Dark</>}
        </button>

        {isLive ? (
          <span className="status-badge status-live">
            <span className="pulse-dot"></span>
            Live On Air
          </span>
        ) : isEnded ? (
          <span className="status-badge status-ended">
            ✓ Broadcast Ended
          </span>
        ) : (
          <span className="status-badge status-draft">
            Draft Setup
          </span>
        )}
      </div>
    </header>
  );
}
