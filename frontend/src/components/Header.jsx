import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Radio, ShieldCheck, Tv, FileText, ExternalLink } from 'lucide-react';

export default function Header({ currentPlan, streamStatus }) {
  const isLive = streamStatus === 'live' || (currentPlan && currentPlan.status === 'live');
  const isEnded = streamStatus === 'ended' || (currentPlan && currentPlan.status === 'ended');

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
          <span>OBS Screen</span>
          <ExternalLink size={13} style={{ opacity: 0.7 }} />
        </a>
      </nav>

      <div className="header-status">
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
