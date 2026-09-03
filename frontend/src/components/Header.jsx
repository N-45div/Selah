import React, { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { Radio, ShieldCheck, Tv, FileText, ExternalLink, Moon, Sun, Monitor, Home, Sparkles } from 'lucide-react';

export default function Header({ currentPlan, streamStatus }) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const location = useLocation();

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
        <div className="brand-icon-wrapper">
          <span className="brand-icon">🕊️</span>
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <h1 className="brand-title">Selah</h1>
            <span className="brand-version-pill">COPILOT</span>
          </div>
          <p className="brand-tagline">Live Telecast & Rights Intelligence</p>
        </div>
      </Link>

      <nav className="header-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <Home size={16} />
          <span>Home</span>
        </NavLink>

        <NavLink to="/prepare" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <ShieldCheck size={16} />
          <span>1. Prepare & License</span>
        </NavLink>

        <NavLink to="/console" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Radio size={16} />
          <span>2. Live Console</span>
        </NavLink>

        <NavLink to="/closeout" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileText size={16} />
          <span>3. Close-Out</span>
        </NavLink>

        <div className="nav-divider" />

        <a 
          href="/output" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link nav-link-external"
          title="Open OBS / vMix Output Window"
        >
          <Tv size={15} />
          <span>OBS Feed</span>
          <ExternalLink size={12} style={{ opacity: 0.6 }} />
        </a>

        <a 
          href="/stage" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link nav-link-external"
          title="Open Stage Confidence Monitor for vocalists"
        >
          <Monitor size={15} color="var(--amber-accent)" />
          <span>Stage HUD</span>
          <ExternalLink size={12} style={{ opacity: 0.6 }} />
        </a>
      </nav>

      <div className="header-status">
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title="Toggle Studio Dark Booth Mode"
        >
          {isDarkMode ? <><Sun size={14} color="#f0c56e" /> Paper Mode</> : <><Moon size={14} /> Studio Dark</>}
        </button>

        {isLive ? (
          <span className="status-badge status-live">
            <span className="pulse-dot"></span>
            LIVE ON AIR
          </span>
        ) : isEnded ? (
          <span className="status-badge status-ended">
            ✓ ENDED
          </span>
        ) : (
          <span className="status-badge status-draft">
            DRAFT
          </span>
        )}
      </div>
    </header>
  );
}
