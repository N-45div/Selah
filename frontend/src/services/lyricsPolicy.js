export const isRestricted = (slide) =>
  Boolean(slide?.legal_status && slide.legal_status !== 'public_domain' && slide.lyrics_policy !== 'full');

export const visibleLines = (slide) =>
  isRestricted(slide) ? (slide?.lines || []).slice(0, 1) : (slide?.lines || []);

export const songSelectUrl = (slide) =>
  slide?.ccli_number
    ? `https://songselect.ccli.com/songs/${slide.ccli_number}`
    : `https://songselect.ccli.com/search/results?search=${encodeURIComponent(slide?.song_title || '')}`;
