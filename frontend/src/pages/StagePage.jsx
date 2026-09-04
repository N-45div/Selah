import React, { useState, useEffect } from 'react';
import { Clock, Radio, Music, VolumeX, ShieldAlert } from 'lucide-react';
import { isRestricted, visibleLines, songSelectUrl } from '../services/lyricsPolicy';

export default function StagePage() {
  const [currentSlide, setCurrentSlide] = useState(null);
  const [nextSlide, setNextSlide] = useState(null);
  const [songInfo, setSongInfo] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const [isBlackout, setIsBlackout] = useState(false);
  const [isAudioMuted, setIsAudioMuted] = useState(false);

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
        } else if (event.data?.type === 'AUDIO_MUTE_TOGGLE') {
          setIsAudioMuted(event.data.isMuted);
        } else if (event.data?.type === 'SLIDE_CHANGE' && event.data.slide) {
          setCurrentSlide(event.data.slide);
          setNextSlide(event.data.nextSlide || null);
          setSongInfo(`${event.data.slide.song_title || ''} • ${event.data.slide.label || ''}`);
        }
      };
      bc.postMessage({ type: 'REQUEST_STATE' });
    } catch (e) {
      console.warn('BroadcastChannel error in StagePage:', e);
    }

    return () => {
      if (bc) bc.close();
    };
  }, []);


  if (isBlackout) {
    return (
      <div style={{ backgroundColor: '#000000', width: '100vw', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555550', fontFamily: 'Inter, sans-serif', fontSize: '2vw', letterSpacing: '0.1em' }}>
        [ SANCTUARY & BROADCAST BLACKOUT ACTIVE ]
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
        padding: '2vw 3.5vw',
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
          paddingBottom: '1.2vw',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1vw' }}>
          <div style={{ background: '#1e2820', padding: '0.6vw', borderRadius: '8px', border: '1px solid #3d6b50' }}>
            <Music size={26} color="#4e8a66" />
          </div>
          <div>
            <div style={{ fontSize: '1.7vw', fontWeight: 700, color: '#f5f2eb' }}>
              {songInfo || 'Selah Stage Confidence Monitor'}
            </div>
            <div style={{ fontSize: '0.95vw', color: '#807a70', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Worship Team Stage View • 0ms Local Sync
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.2vw' }}>
          {isAudioMuted && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4vw', background: '#3b120f', border: '1px solid #a33f2e', color: '#fca5a5', padding: '0.5vw 1vw', borderRadius: '8px', fontSize: '1vw', fontWeight: 700, animation: 'pulse 1.5s infinite' }}>
              <VolumeX size={18} />
              LIVESTREAM AUDIO MUTED (SAFE MODE)
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5vw', background: '#1c1b18', padding: '0.5vw 1.2vw', borderRadius: '8px', border: '1px solid #38342c' }}>
            <Clock size={20} color="#d4912a" />
            <span style={{ fontSize: '1.5vw', fontWeight: 700, color: '#f5f2eb', fontVariantNumeric: 'tabular-nums' }}>
              {currentTime}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4vw', background: '#2d1411', padding: '0.5vw 1vw', borderRadius: '8px', border: '1px solid #59231c', color: '#f08e84', fontSize: '1vw', fontWeight: 700, letterSpacing: '0.05em' }}>
            <Radio size={16} /> LIVE ON AIR
          </div>
        </div>
      </div>

      {/* Main Center Area: Current Lyrics (Huge White Serif) */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '1.5vw 0' }}>
        {currentSlide ? (
          <div>
            {currentSlide.label && (
              <div style={{ display: 'inline-block', background: '#2d2210', border: '1px solid #59421a', color: '#f0c56e', padding: '0.3vw 0.8vw', borderRadius: '6px', fontSize: '1.1vw', fontWeight: 700, textTransform: 'uppercase', marginBottom: '1vw', letterSpacing: '0.06em' }}>
                [{currentSlide.label}]
              </div>
            )}
            
            <div
              style={{
                fontFamily: '"Lora", "Georgia", serif',
                fontSize: '4.5vw',
                fontWeight: 600,
                lineHeight: 1.25,
                color: '#ffffff',
                textShadow: '0 2px 14px rgba(0,0,0,0.9)',
              }}
            >
              {visibleLines(currentSlide).map((line, idx) => (
                <div key={idx} style={{ margin: '0.4vw 0' }}>{line}</div>
              ))}
            </div>

            {isRestricted(currentSlide) && (
              <div style={{ fontSize: '1.2vw', color: '#a09c94', marginTop: '0.8vw', fontFamily: 'Inter, sans-serif' }}>
                Licensed lyrics — <a href={songSelectUrl(currentSlide)} target="_blank" rel="noreferrer" style={{ color: '#d4912a', textDecoration: 'underline' }}>CCLI SongSelect</a>
              </div>
            )}


            {currentSlide.transliteration?.length > 0 && (
              <div
                style={{
                  fontSize: '2.2vw',
                  color: '#d4912a',
                  fontStyle: 'italic',
                  marginTop: '1.2vw',
                  letterSpacing: '0.02em',
                  fontFamily: 'Inter, sans-serif'
                }}
              >
                {currentSlide.transliteration.map((tLine, idx) => (
                  <div key={idx}>{tLine}</div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#666056', fontSize: '2.2vw' }}>
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
            fontSize: '0.95vw',
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
          {nextSlide ? (
            <>
              {nextSlide.label ? `[${nextSlide.label}] ` : ''}
              {nextSlide.lines?.join(' / ')}
            </>
          ) : (
            '(End of Song / Service)'
          )}
        </span>
      </div>
    </div>
  );
}
