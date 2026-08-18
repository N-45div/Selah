import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, Copy, Check, Download, ShieldCheck, 
  Video, RefreshCw, ArrowLeft 
} from 'lucide-react';


export default function CloseoutPage({ plan }) {
  const [closeoutData, setCloseoutData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);

  // Fetch closeout pack data
  useEffect(() => {
    if (!plan?.id) return;
    setIsLoading(true);

    fetch(`/api/plan/${plan.id}/closeout`)
      .then((res) => res.json())
      .then((data) => {
        setCloseoutData(data);
      })
      .catch((err) => {
        console.error('Error fetching closeout pack:', err);
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
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleDownloadMarkdown}
              disabled={!closeoutData}
            >
              <Download size={16} />
              <span>Download Close-Out Pack (.md)</span>
            </button>
            <Link to="/" className="btn btn-secondary">
              <ArrowLeft size={16} />
              <span>New Plan</span>
            </Link>
          </div>
        </div>
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--ink-muted)' }}>
          <RefreshCw className="spin" size={28} style={{ margin: '0 auto 0.75rem' }} />
          <p>Compiling compliance documentation with Gemini...</p>
        </div>
      )}

      {closeoutData && (
        <div className="grid-2">
          {/* Card 1: YouTube Description */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
                <Video size={18} color="#c4302b" />
                1. YouTube Video Description
              </h3>
            </div>
            <p className="card-subtitle">
              Includes mandatory CCLI song attributions required for live stream legal compliance.
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

          {/* Card 2: YouTube Chapters */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <Video size={18} color="#c4302b" />
              2. Timestamped Chapters
            </h3>
            <p className="card-subtitle">
              Formatted for YouTube video description chapters (starting at 0:00).
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

          {/* Card 3: CCLI Usage Reporting Log */}
          <div className="card">
            <h3 className="card-title" style={{ fontSize: '1.1rem' }}>
              <ShieldCheck size={18} color="var(--green-accent)" />
              3. CCLI Usage Reporting Log
            </h3>
            <p className="card-subtitle">
              Ready to transcribe into the church's quarterly CCLI Reporting Portal.
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
              Pre-drafted legal statements with cited sources to paste if a copyright claim lands.
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
