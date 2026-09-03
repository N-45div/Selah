import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, Upload, Sparkles, AlertTriangle, CheckCircle, 
  HelpCircle, ExternalLink, RefreshCw, Layers, ArrowRight, Music 
} from 'lucide-react';

const LICENSE_OPTIONS = [
  { id: 'ccli_copy', label: 'CCLI Copyright License (In-person projection only)' },
  { id: 'ccli_stream', label: 'CCLI Streaming License (Online streaming coverage)' },
  { id: 'ccli_stream_plus', label: 'CCLI Streaming Plus License (Commercial master tracks)' },
  { id: 'onelicense', label: 'OneLicense (Liturgical catalog streaming)' },
];

export default function PreparePage({ plan, setPlan }) {
  const navigate = useNavigate();

  const [serviceName, setServiceName] = useState(plan?.service_name || 'Sunday Morning Worship');
  const [streamTitle, setStreamTitle] = useState(plan?.stream_title || 'Sunday Morning Service & Sermon');
  const [selectedLicenses, setSelectedLicenses] = useState(
    plan?.licenses_held || ['CCLI Copyright License']
  );
  const [language, setLanguage] = useState(plan?.languages?.[0] || 'English');
  const [setlistText, setSetlistText] = useState(
    `1. In Christ Alone - Keith Getty & Stuart Townend\n2. Amazing Grace - John Newton\n3. 10,000 Reasons (Bless The Lord) - Matt Redman\n4. Enakkai Jeevan Vittavare (Tamil Worship)`
  );
  const [imageFile, setImageFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGeneratingSlides, setIsGeneratingSlides] = useState(false);
  const [activeModalSong, setActiveModalSong] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Handle License Toggle
  const toggleLicense = (label) => {
    if (selectedLicenses.includes(label)) {
      setSelectedLicenses(selectedLicenses.filter((l) => l !== label));
    } else {
      setSelectedLicenses([...selectedLicenses, label]);
    }
  };

  // Poll plan status while songs are pending research
  useEffect(() => {
    if (!plan?.id) return;

    const hasPending = plan.songs?.some((s) => s.research_status === 'pending');
    if (!hasPending) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/plan/${plan.id}`);
        if (res.ok) {
          const data = await res.json();
          setPlan(data.plan);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [plan?.id, plan?.songs, setPlan]);

  // Submit Setlist for intake & progressive licensing research
  const handleSubmitSetlist = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      if (imageFile) {
        formData.append('image_file', imageFile);
      } else {
        formData.append('setlist_text', setlistText);
      }
      formData.append('service_name', serviceName);
      formData.append('stream_title', streamTitle);
      formData.append('licenses_held', selectedLicenses.join(','));
      formData.append('languages', language);

      const res = await fetch('/api/plan', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to initialize service plan.');
      }

      const initData = await res.json();

      // Fetch initial created plan state
      const planRes = await fetch(`/api/plan/${initData.plan_id}`);
      if (planRes.ok) {
        const fullData = await planRes.json();
        setPlan(fullData.plan);
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Resolve blocking song with human choice
  const handleResolveSong = async (songIndex, choice) => {
    if (!plan?.id) return;
    try {
      const res = await fetch(`/api/plan/${plan.id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ song_index: songIndex, resolution: choice }),
      });

      if (res.ok) {
        const updatedRes = await fetch(`/api/plan/${plan.id}`);
        const updated = await updatedRes.json();
        setPlan(updated.plan);
        setActiveModalSong(null);
      }
    } catch (err) {
      console.error('Error resolving song:', err);
    }
  };

  // Trigger Slide Pack Generation
  const handleGenerateSlides = async () => {
    if (!plan?.id) return;
    setIsGeneratingSlides(true);
    try {
      const res = await fetch(`/api/plan/${plan.id}/slides`, {
        method: 'POST',
      });
      if (res.ok) {
        const updatedRes = await fetch(`/api/plan/${plan.id}`);
        const updated = await updatedRes.json();
        setPlan(updated.plan);
      }
    } catch (err) {
      console.error('Error generating slides:', err);
    } finally {
      setIsGeneratingSlides(false);
    }
  };

  const blockingSongs = plan?.songs?.filter(
    (s) =>
      (s.verdict?.legal_status === 'needs_license' ||
        s.verdict?.legal_status === 'unknown' ||
        s.research_status === 'error') &&
      !s.resolution
  ) || [];

  const allResearchDone =
    plan?.songs?.length > 0 &&
    plan.songs.every((s) => s.research_status === 'done' || s.research_status === 'error');

  const totalSlides = plan?.songs?.reduce((acc, s) => acc + (s.slides?.length || 0), 0) || 0;

  return (
    <div className="main-container">
      {/* Introduction Card */}
      <div className="card" style={{ borderLeft: '5px solid var(--green-accent)' }}>
        <h2 className="card-title">
          <ShieldCheck size={22} color="var(--green-accent)" />
          Act 1 — Setlist Intake & Licensing Rights Guard
        </h2>
        <p className="card-subtitle" style={{ marginBottom: 0 }}>
          Selah evaluates both music publishing rights (CCLI) and automated YouTube Content ID claim risks.
          <em> Selah never substitutes songs — it gives church volunteers clear choices to keep the broadcast legal and live.</em>
        </p>
      </div>

      <div className="grid-2">
        {/* Left Column: Intake Form */}
        <div className="card">
          <h3 className="card-title">
            <Music size={19} />
            1. Service Setup & Setlist
          </h3>
          <p className="card-subtitle">Paste Sunday's songs or drop a handwritten photo from the worship team.</p>

          <form onSubmit={handleSubmitSetlist}>
            <div className="form-group">
              <label className="form-label">Service Name</label>
              <input
                type="text"
                className="form-input"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. Sunday Morning Worship"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Livestream Title</label>
              <input
                type="text"
                className="form-input"
                value={streamTitle}
                onChange={(e) => setStreamTitle(e.target.value)}
                placeholder="e.g. Sunday Morning Worship & Sermon"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Licenses Currently Held by Church</label>
              <div className="checkbox-group">
                {LICENSE_OPTIONS.map((lic) => (
                  <label key={lic.id} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedLicenses.includes(lic.label.split(' (')[0])}
                      onChange={() => toggleLicense(lic.label.split(' (')[0])}
                    />
                    <span>{lic.label}</span>
                  </label>
                ))}
              </div>
              <p className="form-help">
                Notice: CCLI Copyright License covers in-person projection only. Online streaming requires the CCLI Streaming License.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Primary Language</label>
              <select
                className="form-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="English">English</option>
                <option value="Tamil">Tamil (தமிழ் with Transliteration)</option>
                <option value="Malayalam">Malayalam (മലയാളം with Transliteration)</option>
                <option value="Hindi">Hindi (हिंदी with Transliteration)</option>
                <option value="Telugu">Telugu (తెలుగు with Transliteration)</option>
                <option value="Spanish">Spanish</option>
              </select>
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <label className="form-label" style={{ margin: 0 }}>Setlist Songs (Pasted Text or PCO Format)</label>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--amber-accent)' }}>⚡ Quick Presets for Judges:</span>
              </div>

              {/* Hackathon Judge 1-Click Demo Presets */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  style={{ fontSize: '0.72rem', padding: '0.2rem 0.6rem' }}
                  onClick={() => {
                    setServiceName('Sunday Praise & Broadcast Guard');
                    setSelectedLicenses(['CCLI Copyright License']);
                    setLanguage('English');
                    setSetlistText('1. In Christ Alone - Keith Getty & Stuart Townend\n2. Amazing Grace - John Newton\n3. Way Maker - Sinach');
                    setImageFile(null);
                  }}
                >
                  🎯 Benchmark (TC-01 Red Guard + TC-02 PD)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  style={{ fontSize: '0.72rem', padding: '0.2rem 0.6rem' }}
                  onClick={() => {
                    setServiceName('Diaspora Bilingual Telecast');
                    setSelectedLicenses(['CCLI Streaming License']);
                    setLanguage('Tamil');
                    setSetlistText('1. Enakkai Jeevan Vittavare (Tamil Worship)\n2. 10,000 Reasons (Bless The Lord) - Matt Redman\n3. How Great Thou Art - Stuart K. Hine');
                    setImageFile(null);
                  }}
                >
                  🌐 Diaspora Bilingual (Tamil + English)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  style={{ fontSize: '0.72rem', padding: '0.2rem 0.6rem' }}
                  onClick={() => {
                    setServiceName('Sunday Medley Telecast');
                    setSelectedLicenses(['CCLI Streaming License']);
                    setLanguage('English');
                    setSetlistText('1. Way Maker / Great Are You Lord (Medley)\n2. Blessed Assurance -> King of Kings\n3. Holy Holy Holy - Reginald Heber');
                    setImageFile(null);
                  }}
                >
                  🔀 Medley Decomposer (Slash/Arrow Split)
                </button>
              </div>

              <textarea
                className="form-textarea"
                value={setlistText}
                onChange={(e) => {
                  setSetlistText(e.target.value);
                  setImageFile(null);
                }}
                placeholder="Paste song titles, authors, Planning Center format, or hymns..."
                rows={5}
              />
            </div>


            <div className="form-group">
              <label className="form-label">OR Upload Handwritten Setlist Photo</label>
              <label className="drop-zone" style={{ display: 'block' }}>
                <Upload size={24} style={{ opacity: 0.7, margin: '0 auto 0.4rem' }} />
                <p style={{ fontSize: '0.85rem', fontWeight: 500 }}>
                  {imageFile ? imageFile.name : 'Click to select or drop setlist photo'}
                </p>
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setImageFile(e.target.files[0]);
                      setSetlistText('');
                    }
                  }}
                />
              </label>
            </div>

            {errorMsg && (
              <div style={{ color: 'var(--red-accent)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {errorMsg}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-large btn-block"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="spin" size={18} />
                  Analyzing Setlist with Gemini & Parallel...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Run Autonomous Rights & Content ID Research
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Progressive Verdict Cards */}
        <div>
          {/* Go Live Guard Alert */}
          {plan?.songs?.length > 0 && (
            <div className={`guard-banner ${!allResearchDone ? '' : blockingSongs.length === 0 ? 'clean' : ''}`}>
              <div>
                <strong style={{ display: 'block', fontSize: '0.95rem' }}>
                  {!allResearchDone
                    ? '🔄 Autonomous Research In Progress...'
                    : blockingSongs.length === 0
                    ? '✓ Pre-Broadcast Rights Verified'
                    : `⚠️ ${blockingSongs.length} song${blockingSongs.length > 1 ? 's need' : ' needs'} a decision`}
                </strong>
                <span style={{ fontSize: '0.82rem' }}>
                  {!allResearchDone
                    ? 'Research is still running. The Go-Live guard will not clear until all songs are evaluated.'
                    : blockingSongs.length === 0
                    ? 'All songs are covered or resolved. You are cleared for live broadcast.'
                    : 'Resolve red/unknown songs below before going live to protect against Content ID mutes.'}
                </span>
              </div>
            </div>
          )}

          {/* Cards List */}
          <div className="card">
            <h3 className="card-title">
              <ShieldCheck size={19} />
              2. Progressive Licensing & Content ID Stream
            </h3>
            <p className="card-subtitle">
              Live two-axis verdicts powered by Google ADK + Parallel Search.
            </p>

            {(!plan || !plan.songs || plan.songs.length === 0) && (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--ink-muted)' }}>
                <Music size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
                <p>Submit a setlist on the left to begin autonomous copyright research.</p>
              </div>
            )}

            <div className="verdict-list">
              {plan?.songs?.map((song) => {
                const isPending = song.research_status === 'pending';
                const isError = song.research_status === 'error';
                const v = song.verdict;
                const status = isError ? 'error' : v?.legal_status || 'unknown';

                return (
                  <div
                    key={song.index}
                    className={`verdict-card status-${status}`}
                  >
                    <div className="verdict-header">
                      <div className="song-title-group">
                        <span className="song-num">#{song.index + 1}</span>
                        <div>
                          <h4 className="song-title">{song.title}</h4>
                          <span className="song-artist">
                            {song.artist_or_source || 'Traditional / Congregational'} ({song.language})
                          </span>
                        </div>
                      </div>

                      <div className="pill-group">
                        {isPending ? (
                          <span className="pill pill-neutral">
                            <RefreshCw size={12} className="spin" />
                            Researching...
                          </span>
                        ) : status === 'covered' ? (
                          <span className="pill pill-green">
                            <CheckCircle size={12} /> Covered
                          </span>
                        ) : status === 'public_domain' ? (
                          <span className="pill pill-amber">
                            <CheckCircle size={12} /> Public Domain
                          </span>
                        ) : (
                          <span className="pill pill-red">
                            <AlertTriangle size={12} /> Needs License
                          </span>
                        )}

                        {v && (
                          <span
                            className={`pill ${
                              v.content_id_risk === 'low'
                                ? 'pill-green'
                                : v.content_id_risk === 'medium'
                                ? 'pill-amber'
                                : 'pill-red'
                            }`}
                          >
                            Content ID: {v.content_id_risk.toUpperCase()}
                          </span>
                        )}
                      </div>
                    </div>

                    {isPending ? (
                      <div style={{ padding: '0.75rem 0' }}>
                        <div style={{ color: 'var(--ink-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                          Autonomous agent is investigating publishing rights, CCLI catalog, and YouTube strike risk...
                        </div>
                        <div className="thought-trace">
                          <RefreshCw size={13} className="spin" color="var(--green-accent)" />
                          <span>
                            <strong>Parallel Search:</strong> Querying CCLI SongSelect & YouTube Content ID knowledge base...
                          </span>
                        </div>
                      </div>
                    ) : isError ? (
                      <div style={{ color: 'var(--red-accent)', fontSize: '0.85rem' }}>
                        Research could not complete: {song.error_message}. You can manually choose a resolution.
                      </div>
                    ) : v ? (
                      <>
                        <div className="verdict-metadata">
                          <span><strong>Owner:</strong> {v.owner || 'Unspecified'}</span>
                          {v.ccli_number && <span><strong>CCLI #:</strong> {v.ccli_number}</span>}
                          <span><strong>Language:</strong> {song.language}</span>
                        </div>

                        <div className="verdict-body">
                          <p><strong>Publishing Rights:</strong> {v.legal_summary}</p>
                          <p style={{ marginTop: '0.4rem' }}>
                            <strong>YouTube Content ID Risk:</strong> {v.content_id_summary}
                          </p>
                        </div>

                        {v.sources?.length > 0 && (
                          <div className="verdict-sources">
                            <span style={{ fontWeight: 600, marginRight: '0.5rem' }}>Sources:</span>
                            {v.sources.map((src, i) => (
                              <a
                                key={i}
                                href={src.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="source-link"
                                title={src.note}
                              >
                                {src.title || 'Source'}
                                <ExternalLink size={11} />
                              </a>
                            ))}
                          </div>
                        )}

                        {/* Resolution Bar for Red/Unknown songs */}
                        {(status === 'needs_license' || status === 'unknown') && !song.resolution && (
                          <div className="resolution-bar">
                            <span style={{ fontSize: '0.84rem', color: 'var(--amber-ink)' }}>
                              Action required to unblock Go-Live.
                            </span>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              style={{ fontSize: '0.82rem', padding: '0.35rem 0.75rem' }}
                              onClick={() => setActiveModalSong(song)}
                            >
                              Choose Resolution
                            </button>
                          </div>
                        )}

                        {song.resolution && (
                          <div className="resolved-indicator">
                            ✓ Resolved: {song.resolution}
                          </div>
                        )}
                      </>
                    ) : null}
                  </div>
                );
              })}
            </div>

            {/* Slide Pack Generation & Next Action */}
            {allResearchDone && (
              <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.05rem', fontWeight: 600 }}>
                      3. Slide Pack & Projection Builder
                    </h4>
                    <p style={{ fontSize: '0.84rem', color: 'var(--ink-secondary)' }}>
                      {totalSlides > 0
                        ? `${totalSlides} slides built with proofreading & transliteration.`
                        : 'Generate slides respecting lyrics copyright policy and diaspora transliteration.'}
                    </p>
                  </div>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleGenerateSlides}
                    disabled={isGeneratingSlides}
                  >
                    <Layers size={16} />
                    {isGeneratingSlides ? 'Building Slides...' : totalSlides > 0 ? 'Rebuild Slides' : 'Build Slide Pack'}
                  </button>
                </div>

                <div style={{ marginTop: '1.25rem' }}>
                  <button
                    type="button"
                    className="btn btn-primary btn-large btn-block"
                    onClick={() => navigate('/console')}
                    disabled={blockingSongs.length > 0}
                  >
                    <span>Proceed to Live Broadcast Console</span>
                    <ArrowRight size={18} />
                  </button>
                  {blockingSongs.length > 0 && (
                    <p style={{ fontSize: '0.78rem', color: 'var(--red-accent)', textAlign: 'center', marginTop: '0.4rem' }}>
                      Please resolve all {blockingSongs.length} red/unknown songs above before proceeding.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Resolution Modal */}
      {activeModalSong && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3 className="card-title">
              <AlertTriangle size={20} color="var(--amber-accent)" />
              Operational Options: "{activeModalSong.title}"
            </h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--ink-secondary)', margin: '0.5rem 0 1rem' }}>
              Selah never substitutes songs picked by the worship leader. Please select how the broadcast team will handle this song:
            </p>

            <div className="option-list">
              {activeModalSong.verdict?.options?.length > 0 ? (
                activeModalSong.verdict.options.map((opt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="option-btn"
                    onClick={() => handleResolveSong(activeModalSong.index, opt)}
                  >
                    <strong>Option {idx + 1}:</strong> {opt}
                  </button>
                ))
              ) : (
                <>
                  <button
                    type="button"
                    className="option-btn"
                    onClick={() =>
                      handleResolveSong(
                        activeModalSong.index,
                        'Mute livestream audio output during this song'
                      )
                    }
                  >
                    <strong>Mute Audio:</strong> Mute livestream audio during this song while presenting lyrics
                  </button>
                  <button
                    type="button"
                    className="option-btn"
                    onClick={() =>
                      handleResolveSong(
                        activeModalSong.index,
                        'Church confirmed CCLI Streaming license tier coverage directly'
                      )
                    }
                  >
                    <strong>Confirm License:</strong> Church administrator confirmed streaming license coverage
                  </button>
                </>
              )}
            </div>

            <div style={{ textAlign: 'right', marginTop: '1rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setActiveModalSong(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
