import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { isRestricted, visibleLines, songSelectUrl } from '../services/lyricsPolicy';

export default function OutputPage() {
  const [searchParams] = useSearchParams();
  const isLowerThird = searchParams.get('mode') === 'lower-third';

  const [currentSlide, setCurrentSlide] = useState(null);
  const [songInfo, setSongInfo] = useState('');
  const [isBlackout, setIsBlackout] = useState(false);

  // Set transparent background on body/html for OBS lower-third
  useEffect(() => {
    if (!isLowerThird) return;
    const prevBody = document.body.style.backgroundColor;
    const prevHtml = document.documentElement.style.backgroundColor;
    document.body.style.backgroundColor = 'transparent';
    document.documentElement.style.backgroundColor = 'transparent';
    return () => {
      document.body.style.backgroundColor = prevBody;
      document.documentElement.style.backgroundColor = prevHtml;
    };
  }, [isLowerThird]);

  // Dual Sync Engine: 0ms BroadcastChannel (local booth PC) + SSE fallback (network / OBS machines)
  useEffect(() => {
    let lastBcMessageTime = 0;
    let bc = null;
    let es = null;

    // 1. Primary: 0ms Local BroadcastChannel for same-workstation displays
    try {
      bc = new BroadcastChannel('selah_stream');
      bc.onmessage = (event) => {
        lastBcMessageTime = Date.now();
        if (event.data?.type === 'BLACKOUT_TOGGLE') {
          setIsBlackout(event.data.isBlackout);
        } else if (event.data?.type === 'SLIDE_CHANGE' && event.data.slide) {
          setCurrentSlide(event.data.slide);
          setSongInfo(`${event.data.slide.song_title || ''} • ${event.data.slide.label || ''}`);
        }
      };
      bc.postMessage({ type: 'REQUEST_STATE' });
    } catch (e) {
      console.warn('BroadcastChannel error in OutputPage:', e);
    }

    // 2. Secondary: SSE Server Stream for cross-PC LAN / OBS displays
    const planIdParam = searchParams.get('plan');
    const setupSseFallback = (targetPlanId) => {
      if (!targetPlanId) return;
      try {
        es = new EventSource(`/api/plan/${targetPlanId}/stream`);
        es.addEventListener('plan_update', (e) => {
          // If local BroadcastChannel has recently provided state (< 800ms), let it take 0ms precedence
          if (Date.now() - lastBcMessageTime < 800) return;
          try {
            const data = JSON.parse(e.data);
            if (data.active_slide) {
              setCurrentSlide(data.active_slide);
              setSongInfo(`${data.active_slide.song_title || ''} • ${data.active_slide.label || ''}`);
            }
          } catch (err) {
            console.warn('SSE parse notice in OutputPage:', err);
          }
        });
      } catch (err) {
        console.warn('EventSource initialization notice in OutputPage:', err);
      }
    };

    const resolvedPlanId = planIdParam || localStorage.getItem('selah_current_plan_id');
    if (resolvedPlanId) {
      setupSseFallback(resolvedPlanId);
    } else {
      fetch('/api/plan/active/latest')
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (data?.plan?.id) {
            setupSseFallback(data.plan.id);
          }
        })
        .catch(() => {});
    }

    return () => {
      if (bc) bc.close();
      if (es) es.close();
    };
  }, [searchParams]);

  if (isBlackout) {
    return isLowerThird ? null : (
      <div style={{ backgroundColor: '#000000', width: '100vw', height: '100vh' }} />
    );
  }

  // --- 1. OBS / vMix Transparent Lower-Third Overlay Mode ---
  if (isLowerThird) {
    return (
      <div
        style={{
          backgroundColor: 'transparent',
          width: '100vw',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          padding: '0 5vw 4vh',
          boxSizing: 'border-box',
          overflow: 'hidden',
          userSelect: 'none',
        }}
      >
        {currentSlide && (
          <div
            style={{
              background: 'linear-gradient(180deg, rgba(20, 19, 17, 0.88) 0%, rgba(10, 10, 9, 0.96) 100%)',
              borderLeft: '6px solid #4e8a66',
              borderTop: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '12px',
              padding: '1.5vw 2.5vw',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
              backdropFilter: 'blur(8px)',
              animation: 'fadeIn 0.25s ease-out',
            }}
          >
            {/* Song title badge */}
            <div
              style={{
                fontSize: '0.9vw',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#d4912a',
                fontWeight: 700,
                marginBottom: '0.4vw',
                fontFamily: 'Inter, sans-serif',
              }}
            >
              {songInfo}
            </div>

            {/* Lyric lines */}
            <div
              style={{
                fontFamily: '"Lora", "Georgia", serif',
                fontSize: '2.4vw',
                lineHeight: 1.35,
                fontWeight: 600,
                color: '#ffffff',
                textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              }}
            >
              {visibleLines(currentSlide).slice(0, 2).map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </div>

            {isRestricted(currentSlide) && (
              <div style={{ fontSize: '0.85vw', color: '#a09c94', marginTop: '0.4vw', fontFamily: 'Inter, sans-serif' }}>
                Licensed lyrics — <a href={songSelectUrl(currentSlide)} target="_blank" rel="noreferrer" style={{ color: '#d4912a', textDecoration: 'underline' }}>CCLI SongSelect</a>
              </div>
            )}

            {/* Transliteration */}
            {currentSlide.transliteration?.length > 0 && (
              <div
                style={{
                  fontFamily: 'Inter, sans-serif',
                  fontSize: '1.4vw',
                  color: '#f0c56e',
                  fontStyle: 'italic',
                  marginTop: '0.4vw',
                }}
              >
                {currentSlide.transliteration.slice(0, 2).join(' ')}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }


  // --- 2. Fullscreen Church Projection Mode ---
  return (
    <div
      style={{
        backgroundColor: '#141311',
        color: '#f8f6f0',
        minHeight: '100vh',
        width: '100vw',
        margin: 0,
        padding: '4vw 6vw',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        boxSizing: 'border-box',
        overflow: 'hidden',
        position: 'relative',
        userSelect: 'none',
      }}
    >
      {songInfo && (
        <div
          style={{
            position: 'absolute',
            top: '2vw',
            left: '3vw',
            fontSize: '1.2vw',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#807a70',
            fontFamily: 'Inter, sans-serif',
            fontWeight: 500,
          }}
        >
          {songInfo}
        </div>
      )}

      {currentSlide ? (
        <div style={{ maxWidth: '90vw' }}>
          <div
            style={{
              fontFamily: '"Lora", "Georgia", serif',
              fontSize: '4.2vw',
              lineHeight: 1.35,
              fontWeight: 500,
              letterSpacing: '-0.01em',
              textShadow: '0 2px 10px rgba(0,0,0,0.5)',
              marginBottom: currentSlide.transliteration?.length > 0 ? '1.5vw' : '0',
            }}
          >
            {visibleLines(currentSlide).map((line, idx) => (
              <div key={idx} style={{ margin: '0.4vw 0' }}>{line}</div>
            ))}
          </div>

          {isRestricted(currentSlide) && (
            <div style={{ fontSize: '1.2vw', color: '#a09c94', marginTop: '0.8vw', fontFamily: 'Inter, sans-serif' }}>
              Licensed lyrics — <a href={songSelectUrl(currentSlide)} target="_blank" rel="noreferrer" style={{ color: '#d4912a', textDecoration: 'underline' }}>View in CCLI SongSelect</a>
            </div>
          )}


          {currentSlide.transliteration?.length > 0 && (
            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: '2.5vw',
                color: '#dfc187',
                fontStyle: 'italic',
                fontWeight: 400,
                letterSpacing: '0.02em',
                lineHeight: 1.4,
              }}
            >
              {currentSlide.transliteration.map((tLine, idx) => (
                <div key={idx} style={{ margin: '0.3vw 0' }}>{tLine}</div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', color: '#666056', fontFamily: 'Inter, sans-serif' }}>
          <div style={{ fontSize: '3vw', marginBottom: '1vw' }}>🕊️ Selah Telecast Output</div>
          <div style={{ fontSize: '1.5vw' }}>
            Ready for OBS / vMix Window Capture. Advance slides in the Operator Console.
          </div>
        </div>
      )}
    </div>
  );
}
