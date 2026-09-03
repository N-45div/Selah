import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, Radio, FileText, Sparkles, Tv, Monitor, 
  ArrowRight, CheckCircle2, AlertTriangle, Download, Cpu, 
  Zap, Lock, Eye, Music, Layers, ExternalLink 
} from 'lucide-react';

export default function LandingPage({ setPlan }) {
  const navigate = useNavigate();

  const handleLaunchBenchmark = () => {
    navigate('/prepare');
  };

  return (
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <Sparkles size={16} color="var(--amber-accent)" />
          <span>Google Cloud Agentic Cinema • Parallel Search Partner Track</span>
        </div>

        <h1 className="hero-title">
          The pastor picks the worship.<br />
          <span className="hero-highlight">Selah protects the livestream.</span>
        </h1>

        <p className="hero-subtitle">
          Selah is the autonomous live telecast copilot for church media teams. Powered by <strong>Gemini 3.5 Flash</strong> and <strong>Parallel Web Search</strong>, it prevents algorithmic copyright mutes on YouTube, synchronizes 3 broadcast screens in 0ms, and automates Sunday compliance.
        </p>

        <div className="hero-actions">
          <button 
            type="button" 
            className="btn btn-primary btn-large"
            onClick={() => navigate('/prepare')}
          >
            <Sparkles size={18} />
            <span>Launch Sunday Telecast Copilot</span>
            <ArrowRight size={18} />
          </button>

          <button 
            type="button" 
            className="btn btn-secondary btn-large"
            onClick={() => navigate('/console')}
          >
            <Radio size={18} />
            <span>Open Live Studio Console</span>
          </button>
        </div>

        {/* Live Metrics Ribbon */}
        <div className="metrics-ribbon">
          <div className="metric-card">
            <span className="metric-val">0ms</span>
            <span className="metric-lbl">Local Screen IPC Sync</span>
          </div>
          <div className="metric-card">
            <span className="metric-val">100%</span>
            <span className="metric-lbl">Google GenAI + Parallel</span>
          </div>
          <div className="metric-card">
            <span className="metric-val">3-Act</span>
            <span className="metric-lbl">End-to-End Workflow</span>
          </div>
          <div className="metric-card">
            <span className="metric-val">$0.00</span>
            <span className="metric-lbl">Idle Cost (Serverless Run)</span>
          </div>
        </div>
      </section>

      {/* The 3 Acts System Showcase */}
      <section className="acts-showcase-section">
        <div className="section-header">
          <h2 className="section-title">A 3-Act Telecast Engine for Sunday Media Booths</h2>
          <p className="section-subtitle">
            From handwritten bulletin intake to live OBS lower-thirds and post-stream dispute kits.
          </p>
        </div>

        <div className="acts-grid">
          {/* Act 1 Card */}
          <div className="act-card">
            <div className="act-card-header">
              <div className="act-badge act-badge-1">ACT 1 • PREPARE</div>
              <ShieldCheck size={26} color="var(--green-accent)" />
            </div>
            <h3 className="act-card-title">Autonomous Rights Guard & Intake</h3>
            <p className="act-card-desc">
              Accepts handwritten setlist photos, text, or Planning Center plans. Gemini and Parallel Web Search evaluate publishing licenses against Content ID risks with grounded citations.
            </p>
            <ul className="act-feature-list">
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> 1-Click Judge Benchmark Presets (TC-01 to TC-05)</li>
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> Human-in-the-Loop Safe Mode Decision Gate</li>
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> Indic Script Latin Phonetic Transliterations</li>
            </ul>
            <div className="act-card-footer">
              <button 
                type="button" 
                className="btn btn-secondary btn-block"
                onClick={() => navigate('/prepare')}
              >
                Explore Act 1 Intake & Guard →
              </button>
            </div>
          </div>

          {/* Act 2 Card */}
          <div className="act-card featured-act-card">
            <div className="act-card-header">
              <div className="act-badge act-badge-2">ACT 2 • TELECAST</div>
              <Radio size={26} color="var(--amber-accent)" />
            </div>
            <h3 className="act-card-title">Live Studio Multi-View Console</h3>
            <p className="act-card-desc">
              Zero-latency local synchronization for multi-monitor broadcast booths. Controls the sanctuary screen, transparent OBS lower-thirds, and stage confidence HUD simultaneously.
            </p>
            <ul className="act-feature-list">
              <li><CheckCircle2 size={15} color="var(--amber-accent)" /> 0ms BroadcastChannel Local IPC Screen Sync</li>
              <li><CheckCircle2 size={15} color="var(--amber-accent)" /> Studio Multi-View (Projector + Lower-Third + Stage HUD)</li>
              <li><CheckCircle2 size={15} color="var(--amber-accent)" /> 1-Click 16:9 PowerPoint (.pptx) & ProPresenter Exporter</li>
            </ul>
            <div className="act-card-footer">
              <button 
                type="button" 
                className="btn btn-primary btn-block"
                onClick={() => navigate('/console')}
              >
                Launch Live Telecast Console →
              </button>
            </div>
          </div>

          {/* Act 3 Card */}
          <div className="act-card">
            <div className="act-card-header">
              <div className="act-badge act-badge-3">ACT 3 • CLOSE-OUT</div>
              <FileText size={26} color="#c4302b" />
            </div>
            <h3 className="act-card-title">Compliance Dossier & Dispute Kit</h3>
            <p className="act-card-desc">
              Automatically compiles legally mandated CCLI song attributions, 0:00 timestamped YouTube chapters, quarterly audit logs, and statutory DMCA § 512(g) counter-notices.
            </p>
            <ul className="act-feature-list">
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> YouTube Description with CCLI Attributions</li>
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> Multi-Platform Dispute Kit (YouTube & Meta)</li>
              <li><CheckCircle2 size={15} color="var(--green-accent)" /> Standalone Markdown & PDF Compliance Export</li>
            </ul>
            <div className="act-card-footer">
              <button 
                type="button" 
                className="btn btn-secondary btn-block"
                onClick={() => navigate('/closeout')}
              >
                View Close-Out & Dispute Kit →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Live Display Sandbox Previews */}
      <section className="displays-section">
        <div className="section-header">
          <h2 className="section-title">Dedicated Hardware & Broadcast Displays</h2>
          <p className="section-subtitle">
            Open dedicated browser windows on secondary graphics cards or OBS browser sources.
          </p>
        </div>

        <div className="display-links-grid">
          <a href="/output" target="_blank" rel="noopener noreferrer" className="display-preview-card">
            <div className="display-icon-box">
              <Tv size={28} color="#d4912a" />
            </div>
            <div>
              <h4 className="display-card-title">Sanctuary Projector (16:9 Fullscreen)</h4>
              <p className="display-card-desc">Clean high-contrast serif typography for sanctuary congregation singing.</p>
            </div>
            <ExternalLink size={16} className="ext-icon" />
          </a>

          <a href="/output?mode=lower-third" target="_blank" rel="noopener noreferrer" className="display-preview-card">
            <div className="display-icon-box">
              <Monitor size={28} color="#4e8a66" />
            </div>
            <div>
              <h4 className="display-card-title">OBS / vMix Transparent Lower-Third</h4>
              <p className="display-card-desc">Glassmorphic dual-line broadcast overlay with alpha transparency & diaspora sublines.</p>
            </div>
            <ExternalLink size={16} className="ext-icon" />
          </a>

          <a href="/stage" target="_blank" rel="noopener noreferrer" className="display-preview-card">
            <div className="display-icon-box">
              <Music size={28} color="#f0c56e" />
            </div>
            <div>
              <h4 className="display-card-title">Stage Musician Confidence Monitor</h4>
              <p className="display-card-desc">Musician HUD with live digital clock, active verse lyrics, and amber "Next Up" line preview.</p>
            </div>
            <ExternalLink size={16} className="ext-icon" />
          </a>
        </div>
      </section>

      {/* The Core Distinction / Moat */}
      <section className="moat-section">
        <div className="moat-card">
          <div className="moat-header">
            <ShieldCheck size={32} color="var(--green-accent)" />
            <div>
              <h3 className="moat-title">Selah's Hard Product Boundary: Never Replaces Worship</h3>
              <p className="moat-subtitle">
                Traditional AI tools attempt to rewrite setlists or recommend alternative songs. Selah <strong>never modifies or substitutes songs</strong>. Input is always the pastor's exact choice. Red-verdict songs present clear operational choices for volunteers (Safe Mode stream audio mute or CCLI verification) to keep the broadcast legal and live.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
