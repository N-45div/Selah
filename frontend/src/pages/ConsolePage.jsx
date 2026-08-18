import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Radio, Play, Square, ChevronLeft, ChevronRight, Bookmark, 
  Tv, ExternalLink, Clock, Layers, AlertCircle, CheckCircle 
} from 'lucide-react';

const COMMON_CHAPTERS = [
  'Welcome & Opening Worship',
  'Congregational Praise',
  'Pastoral Prayer',
  'Scripture Reading',
  'Sermon / Message',
  'Communion',
  'Benediction & Closing',
];

export default function ConsolePage({ plan, setPlan, setStreamStatus }) {
  const navigate = useNavigate();

  const [currentSlideIndex, setCurrentSlideIndex] = useState(plan?.current_slide_index || 0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [customChapterLabel, setCustomChapterLabel] = useState('');
  const [isGoingLive, setIsGoingLive] = useState(false);
  const [isEnding, setIsEnding] = useState(false);

  // Flatten all slides across songs
  const allSlides = useMemo(() => {
    const flattened = [];
    if (!plan?.songs) return flattened;
    plan.songs.forEach((song) => {
      if (song.slides && song.slides.length > 0) {
        song.slides.forEach((slide) => {
          flattened.push({
            ...slide,
            song_title: song.title,
            song_language: song.language,
          });
        });
      } else {
        // Fallback placeholder slide
        flattened.push({
          song_index: song.index,
          label: 'Title Slide',
          lines: [song.title, song.artist_or_source || 'Worship'],
          transliteration: [],
          song_title: song.title,
          song_language: song.language,
        });
      }
    });
    return flattened;
  }, [plan?.songs]);

  const currentSlide = allSlides[currentSlideIndex] || null;
  const nextSlide = allSlides[currentSlideIndex + 1] || null;

  // BroadcastChannel for instant local syncing to /output screen
  const broadcastChannel = useMemo(() => {
    try {
      return new BroadcastChannel('selah_stream');
    } catch (e) {
      console.warn('BroadcastChannel not supported in this browser.', e);
      return null;
    }
  }, []);

  const syncSlideToOutput = useCallback(
    (index) => {
      if (broadcastChannel && allSlides[index]) {
        broadcastChannel.postMessage({
          type: 'SLIDE_CHANGE',
          slideIndex: index,
          totalSlides: allSlides.length,
          slide: allSlides[index],
        });
      }
    },
    [broadcastChannel, allSlides]
  );

  // Sync on index change
  useEffect(() => {
    syncSlideToOutput(currentSlideIndex);
  }, [currentSlideIndex, syncSlideToOutput]);

  // Elapsed timer when live
  useEffect(() => {
    if (plan?.status !== 'live' || !plan?.started_at) return;

    const startTime = new Date(plan.started_at).getTime();
    const timer = setInterval(() => {
      const diff = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
      setElapsedSeconds(diff);
    }, 1000);

    return () => clearInterval(timer);
  }, [plan?.status, plan?.started_at]);

  // Advance / Previous Slide Handler
  const handleGoToSlide = useCallback(
    async (newIndex) => {
      if (newIndex < 0 || newIndex >= allSlides.length) return;
      setCurrentSlideIndex(newIndex);
      syncSlideToOutput(newIndex);

      if (plan?.id) {
        try {
          await fetch(`/api/plan/${plan.id}/advance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slide_index: newIndex }),
          });
        } catch (err) {
          console.error('Failed to persist slide index:', err);
        }
      }
    },
    [allSlides.length, plan?.id, syncSlideToOutput]
  );

  // Keyboard navigation shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger if typing in an input
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();
        handleGoToSlide(currentSlideIndex + 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        handleGoToSlide(currentSlideIndex - 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentSlideIndex, handleGoToSlide]);

  // Go Live
  const handleGoLive = async () => {
    if (!plan?.id) return;
    setIsGoingLive(true);
    try {
      const res = await fetch(`/api/plan/${plan.id}/live`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setStreamStatus('live');
        const planRes = await fetch(`/api/plan/${plan.id}`);
        const planData = await planRes.json();
        setPlan(planData.plan);
      } else {
        const err = await res.json();
        alert(err.detail || 'Could not go live.');
      }
    } catch (e) {
      console.error('Error going live:', e);
    } finally {
      setIsGoingLive(false);
    }
  };

  // Mark Chapter
  const handleMarkChapter = async (label) => {
    if (!plan?.id || !label.trim()) return;
    try {
      const res = await fetch(`/api/plan/${plan.id}/chapter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label }),
      });
      if (res.ok) {
        const planRes = await fetch(`/api/plan/${plan.id}`);
        const planData = await planRes.json();
        setPlan(planData.plan);
        setCustomChapterLabel('');
      }
    } catch (e) {
      console.error('Error marking chapter:', e);
    }
  };

  // End Stream
  const handleEndStream = async () => {
    if (!plan?.id) return;
    if (!window.confirm('Are you ready to end the stream and generate the post-broadcast closeout pack?')) {
      return;
    }

    setIsEnding(true);
    try {
      const res = await fetch(`/api/plan/${plan.id}/end`, {
        method: 'POST',
      });
      if (res.ok) {
        setStreamStatus('ended');
        navigate('/closeout');
      }
    } catch (e) {
      console.error('Error ending stream:', e);
    } finally {
      setIsEnding(false);
    }
  };

  const formatTimer = (totalSeconds) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs > 0 ? `${hrs}:` : ''}${mins.toString().padStart(2, '0')}:${secs
      .toString()
      .padStart(2, '0')}`;
  };

  const isLive = plan?.status === 'live';
  const blockingCount =
    plan?.songs?.filter(
      (s) =>
        (s.verdict?.legal_status === 'needs_license' ||
          s.verdict?.legal_status === 'unknown' ||
          s.research_status === 'error') &&
        !s.resolution
    ).length || 0;

  return (
    <div className="main-container">
      {/* Top Telecast Banner */}
      <div className="card" style={{ padding: '1.25rem 1.75rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Radio size={24} color={isLive ? 'var(--red-accent)' : 'var(--ink-muted)'} />
            <div>
              <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', fontWeight: 600 }}>
                {plan?.service_name || 'Sunday Service'} — Telecast Console
              </h2>
              <span style={{ fontSize: '0.85rem', color: 'var(--ink-secondary)' }}>
                {plan?.stream_title || 'Livestream'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {isLive ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--red-bg)', padding: '0.4rem 0.9rem', borderRadius: '999px', border: '1px solid var(--red-border)' }}>
                <Clock size={16} color="var(--red-accent)" />
                <strong style={{ color: 'var(--red-ink)', fontSize: '0.95rem' }}>
                  {formatTimer(elapsedSeconds)}
                </strong>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleGoLive}
                disabled={blockingCount > 0 || isGoingLive}
              >
                <Play size={16} />
                {isGoingLive ? 'Starting...' : 'Go Live Now'}
              </button>
            )}

            <a
              href="/output"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary"
              title="Open OBS projection screen in dedicated window"
            >
              <Tv size={16} />
              <span>Open OBS Screen</span>
              <ExternalLink size={13} />
            </a>

            {isLive && (
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleEndStream}
                disabled={isEnding}
              >
                <Square size={16} />
                {isEnding ? 'Closing out...' : 'End Stream'}
              </button>
            )}
          </div>
        </div>

        {blockingCount > 0 && !isLive && (
          <div style={{ marginTop: '0.85rem', padding: '0.6rem 0.85rem', background: 'var(--red-bg)', border: '1px solid var(--red-border)', borderRadius: 'var(--radius)', color: 'var(--red-ink)', fontSize: '0.84rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} />
            <span>
              Go-Live Guard active: {blockingCount} song(s) require licensing resolution in Step 1 before broadcasting.
            </span>
          </div>
        )}
      </div>

      {/* Main Console Split */}
      <div className="live-dashboard">
        {/* Left Column: Live Slide Output & Navigation */}
        <div>
          <div className="slide-viewer">
            <span className="slide-section-label">
              {currentSlide?.song_title} • {currentSlide?.label || 'Slide'} ({currentSlideIndex + 1} / {allSlides.length || 1})
            </span>

            {currentSlide ? (
              <>
                <div className="slide-main-text">
                  {currentSlide.lines?.map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>

                {currentSlide.transliteration?.length > 0 && (
                  <div className="slide-translit-text">
                    {currentSlide.transliteration.map((tLine, idx) => (
                      <div key={idx}>{tLine}</div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div style={{ color: '#a39e94', fontStyle: 'italic' }}>
                No slides loaded. Generate slide pack in Step 1.
              </div>
            )}
          </div>

          {/* Big Tactile Navigation Controls */}
          <div className="console-controls">
            <button
              type="button"
              className="btn btn-secondary btn-large"
              style={{ flex: 1 }}
              onClick={() => handleGoToSlide(currentSlideIndex - 1)}
              disabled={currentSlideIndex <= 0}
            >
              <ChevronLeft size={22} />
              <span>Previous Slide (←)</span>
            </button>

            <button
              type="button"
              className="btn btn-primary btn-large"
              style={{ flex: 1.5 }}
              onClick={() => handleGoToSlide(currentSlideIndex + 1)}
              disabled={currentSlideIndex >= allSlides.length - 1}
            >
              <span>Next Slide (Space / →)</span>
              <ChevronRight size={22} />
            </button>
          </div>

          {/* Upcoming Next Slide Preview */}
          <div className="next-slide-preview">
            <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', marginBottom: '0.35rem' }}>
              Upcoming Next Slide Preview:
            </div>
            {nextSlide ? (
              <div style={{ fontSize: '0.92rem', color: 'var(--ink-secondary)' }}>
                <strong>{nextSlide.song_title} ({nextSlide.label}):</strong>{' '}
                {nextSlide.lines?.join(' / ')}
              </div>
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--ink-muted)', fontStyle: 'italic' }}>
                End of slide pack.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Telecast Chapters & Live Info */}
        <div>
          <div className="card">
            <h3 className="card-title">
              <Bookmark size={18} />
              Live Chapter Markers
            </h3>
            <p className="card-subtitle">
              One-click stamps elapsed time into YouTube chapter format.
            </p>

            <div className="chapter-buttons">
              {COMMON_CHAPTERS.map((label) => (
                <button
                  key={label}
                  type="button"
                  className="btn-chip"
                  onClick={() => handleMarkChapter(label)}
                  disabled={!isLive}
                >
                  + {label}
                </button>
              ))}
            </div>

            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Custom chapter name..."
                value={customChapterLabel}
                onChange={(e) => setCustomChapterLabel(e.target.value)}
                disabled={!isLive}
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => handleMarkChapter(customChapterLabel)}
                disabled={!isLive || !customChapterLabel.trim()}
              >
                Mark
              </button>
            </div>

            {/* Marked Chapters History */}
            <div style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--ink-muted)', marginBottom: '0.5rem' }}>
                Recorded Chapters ({plan?.chapters?.length || 0}):
              </div>

              <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
                {plan?.chapters?.length > 0 ? (
                  plan.chapters.map((ch, idx) => (
                    <div
                      key={idx}
                      style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0', fontSize: '0.84rem', borderBottom: '1px dashed var(--border-color)' }}
                    >
                      <span>{ch.label}</span>
                      <strong style={{ color: 'var(--green-accent)' }}>{ch.timestamp_str}</strong>
                    </div>
                  ))
                ) : (
                  <span style={{ fontSize: '0.82rem', color: 'var(--ink-muted)', fontStyle: 'italic' }}>
                    {isLive ? 'No chapters marked yet.' : 'Chapters will record when live.'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Volunteer Cheatsheet Card */}
          <div className="card" style={{ background: 'var(--bg-subtle)' }}>
            <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: '1rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Keyboard Shortcuts for Media Volunteers
            </h4>
            <ul style={{ fontSize: '0.82rem', color: 'var(--ink-secondary)', paddingLeft: '1.2rem', lineHeight: '1.6' }}>
              <li><strong>Spacebar / Right Arrow (→):</strong> Advance to next slide</li>
              <li><strong>Left Arrow (←):</strong> Return to previous slide</li>
              <li><strong>OBS Window:</strong> Keep <code>/output</code> open on second display</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
