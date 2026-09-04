import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, Copy, Check, Download, ShieldCheck, 
  Video, RefreshCw, ArrowLeft, AlertCircle 
} from 'lucide-react';


export default function CloseoutPage({ plan, isHydrating }) {
  const [closeoutData, setCloseoutData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notReadyMessage, setNotReadyMessage] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);

  // Fetch closeout pack data
  useEffect(() => {
    if (!plan?.id) return;
    setIsLoading(true);
    setNotReadyMessage(null);

    fetch(`/api/plan/${plan.id}/closeout`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (res.status === 409) {
            setNotReadyMessage(data.detail || "Close-out is available after the live telecast ends.");
          } else {
            setNotReadyMessage(data.detail || "Could not load close-out data.");
          }
          setCloseoutData(null);
          return null;
        }
        setCloseoutData(data);
      })
      .catch((err) => {
        console.error('Error fetching closeout pack:', err);
        setNotReadyMessage("Failed to communicate with server.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [plan?.id]);

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => {
      setCopiedKey(null);
    }, 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!plan?.id) return;
    window.location.href = `/api/plan/${plan.id}/closeout/download`;
  };

  if (isHydrating) {
    return (
      <div className="main-container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <p style={{ color: 'var(--ink-muted)' }}>Restoring service plan...</p>
      </div>
    );
  }

  if (!plan?.id) {
    return (
      <div className="main-container">
        <div className="card" style={{ padding: '3rem 2rem', textAlign: 'center', maxWidth: '600px', margin: '2rem auto' }}>
          <h2 className="card-title" style={{ justifyContent: 'center' }}>No Service Plan Loaded</h2>
          <p className="card-subtitle" style={{ marginBottom: '1.5rem' }}>
            Start in Act 1 to intake a setlist and run the broadcast workflow.
          </p>
          <Link to="/prepare" className="btn btn-primary" style={{ display: 'inline-flex' }}>
            Go to Prepare &amp; License
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="main-container">
      {/* Top Banner */}
      <div className="card" style={{ borderLeft: '5px solid var(--green-accent)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 className="card-title">
              <FileText size={22} color="var(--green-accent)" />
              Act 3 — Post-Broadcast Close-Out & Compliance Pack
            </h2>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Complete compliance kit: YouTube description with mandatory CCLI attributions, timestamped chapters, CCLI reporting log, and YouTube Content ID dispute kit.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/console" className="btn btn-outline" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
              <ArrowLeft size={16} /> Back to Console
            </Link>
            {closeoutData && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleDownloadMarkdown}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
              >
                <Download size={16} /> Download Full Markdown Pack (.md)
              </button>
            )}
          </div>
        </div>
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem', color: 'var(--green-accent)' }} />
          <p>Compiling comprehensive compliance close-out pack with Gemini...</p>
        </div>
      )}

      {notReadyMessage && !isLoading && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem', borderLeft: '5px solid var(--amber-accent)' }}>
          <AlertCircle size={32} color="var(--amber-accent)" style={{ margin: '0 auto 0.75rem' }} />
          <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Close-Out Not Yet Available</h3>
          <p style={{ color: 'var(--ink-secondary)', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
            {notReadyMessage}
          </p>
          <Link to="/console" className="btn btn-primary" style={{ display: 'inline-flex' }}>
            Go to Live Studio Console
          </Link>
        </div>
      )}

      {closeoutData && !isLoading && (
        <div className="grid-2">
          {/* Card 1: Ready-to-Paste YouTube Description */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <Video size={18} color="var(--blue-accent)" />
              1. YouTube Video Description & Licensing Attribution
            </h3>
            <p className="card-subtitle">
              Fully compliant YouTube description with mandatory CCLI streaming attributions & public domain notices.
            </p>

            <div className="copy-box-wrapper">
              <button
                type="button"
                className="btn btn-copy"
                onClick={() => handleCopy(closeoutData.youtube_description, 'desc')}
              >
                {copiedKey === 'desc' ? <><Check size={12} color="green" /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
              <textarea
                className="copy-box"
                readOnly
                value={closeoutData.youtube_description}
              />
            </div>
          </div>

          {/* Card 2: Timestamped Chapters */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <FileText size={18} color="var(--green-accent)" />
              2. YouTube Chapter Timestamps
            </h3>
            <p className="card-subtitle">
              Ready-to-paste video chapters marked live from the telecast console (starts with 0:00).
            </p>

            <div className="copy-box-wrapper">
              <button
                type="button"
                className="btn btn-copy"
                onClick={() => handleCopy(closeoutData.chapters_text, 'chapters')}
              >
                {copiedKey === 'chapters' ? <><Check size={12} color="green" /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
              <textarea
                className="copy-box"
                readOnly
                value={closeoutData.chapters_text}
              />
            </div>
          </div>

          {/* Card 3: CCLI Quarterly Usage Log */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <FileText size={18} color="var(--purple-accent)" />
              3. CCLI Quarterly Reporting Table
            </h3>
            <p className="card-subtitle">
              Audit-ready log of all performed songs for quarterly church copyright reporting.
            </p>

            <div className="copy-box-wrapper">
              <button
                type="button"
                className="btn btn-copy"
                onClick={() => handleCopy(closeoutData.ccli_usage_log, 'ccli')}
              >
                {copiedKey === 'ccli' ? <><Check size={12} color="green" /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
              <textarea
                className="copy-box"
                readOnly
                value={closeoutData.ccli_usage_log}
              />
            </div>
          </div>

          {/* Card 4: Content ID Dispute Kit */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <ShieldCheck size={18} color="var(--amber-accent)" />
              4. YouTube Content ID Dispute Kit
            </h3>
            <p className="card-subtitle">
              Draft dispute statements with cited sources. Review each one and confirm your licence before filing.
            </p>

            <div className="copy-box-wrapper">
              <button
                type="button"
                className="btn btn-copy"
                onClick={() => handleCopy(closeoutData.dispute_pack, 'dispute')}
              >
                {copiedKey === 'dispute' ? <><Check size={12} color="green" /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
              <textarea
                className="copy-box"
                readOnly
                value={closeoutData.dispute_pack}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
