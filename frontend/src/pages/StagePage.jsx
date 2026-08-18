import React, { useState, useEffect } from 'react';
import { Clock, Radio, Music } from 'lucide-react';

export default function StagePage() {
  const [currentSlide, setCurrentSlide] = useState(null);
  const [nextSlide, setNextSlide] = useState(null);
  const [songInfo, setSongInfo] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const [isBlackout, setIsBlackout] = useState(false);

  // Clock
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Sync with BroadcastChannel
  useEffect(() => {
    let bc;
    try {
      bc = new BroadcastChannel('selah_stream');
      bc.onmessage = (event) => {
        if (event.data?.type === 'BLACKOUT_TOGGLE') {
          setIsBlackout(event.data.isBlackout);
        } else if (event.data?.type === 'SLIDE_CHANGE' && event.data.slide) {
          setCurrentSlide(event.data.slide);
          setNextSlide(event.data.nextSlide || null);
          setSongInfo(`${event.data.slide.song_title || ''} • ${event.data.slide.label || ''}`);
        }
      };
    } catch (e) {
      console.warn('BroadcastChannel error in StagePage:', e);
    }

    return () => {
      if (bc) bc.close();
    };
  }, []);

  if (isBlackout) {
    return (
      <div style={{ backgroundColor: '#000000', width: '100vw', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#333333', fontFamily: 'Inter, sans-serif' }}>
        [ STAGE SCREEN MUTED / BLACKOUT ]
      </div>
    );
  }

  return (
    <div
      style={{
        backgroundColor: '#0a0a09',
        color: '#ffffff',
        width: '100vw',
        height: '100vh',
        padding: '2.5vw 4vw',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        fontFamily: 'Inter, sans-serif',
        userSelect: 'none',
        overflow: 'hidden',
      }}
    >
      {/* Top HUD Header: Song Title & Live Clock */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '2px solid #262624',
          paddingBottom: '1.5vw',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1vw' }}>
          <Music size={28} color="#4e8a66" />
          <div>
            <div style={{ fontSize: '1.8vw', fontWeight: 700, color: '#f5f2eb' }}>
              {songInfo || 'Selah Stage Confidence Monitor'}
            </div>
            <div style={{ fontSize: '1vw', color: '#807a70', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Worship Team Stage View
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5vw' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5vw', background: '#1c1b18', padding: '0.6vw 1.2vw', borderRadius: '8px', border: '1px solid #38342c' }}>
            <Clock size={20} color="#d4912a" />
            <span style={{ fontSize: '1.6vw', fontWeight: 700, color: '#f5f2eb', fontVariantNumeric: 'tabular-nums' }}>
              {currentTime}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4vw', background: '#2d1411', padding: '0.6vw 1vw', borderRadius: '8px', border: '1px solid #59231c', color: '#f08e84', fontSize: '1vw', fontWeight: 600 }}>
            <Radio size={16} /> LIVE ON AIR
          </div>
        </div>
      </div>

      {/* Main Center Area: Current Lyrics (Huge White Serif) */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '2vw 0' }}>
        {currentSlide ? (
          <div>
            <div
              style={{
                fontFamily: '"Lora", "Georgia", serif',
                fontSize: '4.8vw',
                fontWeight: 600,
                lineHeight: 1.3,
                color: '#ffffff',
                textShadow: '0 2px 12px rgba(0,0,0,0.8)',
              }}
            >
              {currentSlide.lines?.map((line, idx) => (
                <div key={idx} style={{ margin: '0.5vw 0' }}>{line}</div>
              ))}
            </div>

            {currentSlide.transliteration?.length > 0 && (
              <div
                style={{
                  fontSize: '2.4vw',
                  color: '#d4912a',
                  fontStyle: 'italic',
                  marginTop: '1.5vw',
                  letterSpacing: '0.02em',
                }}
              >
                {currentSlide.transliteration.map((tLine, idx) => (
                  <div key={idx}>{tLine}</div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#666056', fontSize: '2.5vw' }}>
            Awaiting lyrics from media booth operator...
          </div>
        )}
      </div>

      {/* Bottom Footer: Next Up Preview (Amber Sand) */}
      <div
        style={{
          backgroundColor: '#161513',
          border: '1px solid #33302a',
          borderRadius: '12px',
          padding: '1.2vw 2vw',
          display: 'flex',
          alignItems: 'center',
          gap: '1.5vw',
        }}
      >
        <span
          style={{
            backgroundColor: '#2d2210',
            color: '#f0c56e',
            border: '1px solid #59421a',
            padding: '0.3vw 0.8vw',
            borderRadius: '6px',
            fontSize: '0.9vw',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          }}
        >
          NEXT UP:
        </span>
        <span
          style={{
            fontSize: '1.6vw',
            color: '#b8b2a5',
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {nextSlide ? nextSlide.lines?.join(' / ') : '(End of Song / Section)'}
        </span>
      </div>
    </div>
  );
}
