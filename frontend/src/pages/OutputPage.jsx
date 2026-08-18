import React, { useState, useEffect } from 'react';

export default function OutputPage() {
  const [currentSlide, setCurrentSlide] = useState(null);
  const [songInfo, setSongInfo] = useState('');

  // 1. Listen for instant BroadcastChannel events from the console tab
  useEffect(() => {
    let bc;
    try {
      bc = new BroadcastChannel('selah_stream');
      bc.onmessage = (event) => {
        if (event.data?.type === 'SLIDE_CHANGE' && event.data.slide) {
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
      {/* Discreet Section Label in top corner */}
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

      {/* Main Lyric Display */}
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
              <div key={idx} style={{ margin: '0.4vw 0' }}>
                {line}
              </div>
            ))}
          </div>

          {/* Transliteration line in gold/sand */}
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
                <div key={idx} style={{ margin: '0.3vw 0' }}>
                  {tLine}
                </div>
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
