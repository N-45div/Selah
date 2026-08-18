import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

export default function OutputPage() {
  const [searchParams] = useSearchParams();
  const isLowerThird = searchParams.get('mode') === 'lower-third';

  const [currentSlide, setCurrentSlide] = useState(null);
  const [songInfo, setSongInfo] = useState('');
  const [isBlackout, setIsBlackout] = useState(false);

  // BroadcastChannel listener
  useEffect(() => {
    let bc;
    try {
      bc = new BroadcastChannel('selah_stream');
      bc.onmessage = (event) => {
        if (event.data?.type === 'BLACKOUT_TOGGLE') {
          setIsBlackout(event.data.isBlackout);
        } else if (event.data?.type === 'SLIDE_CHANGE' && event.data.slide) {
          setCurrentSlide(event.data.slide);
          setSongInfo(`${event.data.slide.song_title || ''} • ${event.data.slide.label || ''}`);
        }
      };
    } catch (e) {
      console.warn('BroadcastChannel error in OutputPage:', e);
    }

    return () => {
      if (bc) bc.close();
    };
  }, []);

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
              {currentSlide.lines?.slice(0, 2).map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </div>

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
            {currentSlide.lines?.map((line, idx) => (
              <div key={idx} style={{ margin: '0.4vw 0' }}>{line}</div>
            ))}
          </div>

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
