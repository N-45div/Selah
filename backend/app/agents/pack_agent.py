from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..services.gemini_client import generate_structured
from ..models import Song, Slide, LegalStatus


class GeneratedSlideItem(BaseModel):
    label: str = Field(description="Section name (e.g. Verse 1, Chorus, Verse 2, Bridge, Outro)")
    lines: List[str] = Field(description="Lyric lines or placeholder text")
    transliteration: List[str] = Field(default_factory=list, description="Latin alphabet transliteration lines if non-Latin script")


class SongPackResult(BaseModel):
    song_index: int
    title: str
    lyrics_policy: str = Field(description="'full' for public domain, 'placeholder' for copyrighted")
    slides: List[GeneratedSlideItem] = Field(description="Structured slide pack for projection")
    proofreading_notes: List[str] = Field(default_factory=list, description="Helpful typo/spelling observations for the media team")


PACK_SYSTEM_INSTRUCTION = """
You are Selah's Worship Slide Pack & Projection Specialist.
Your mission is to generate clean, legible broadcast slides with strict legal compliance, proofreading suggestions, and phonetic transliterations.

LEGAL LYRICS POLICY (MANDATORY):
1. PUBLIC DOMAIN SONGS (`legal_status == 'public_domain'`):
   - You may output standard public domain hymn verses and refrains (e.g., "Amazing grace! how sweet the sound...", "When peace like a river...").
2. COPYRIGHTED / LICENSED SONGS (`legal_status == 'covered'` or `'needs_license'`):
   - DO NOT reproduce or scrape full copyrighted lyrics.
   - Output structured slide templates with section labels and placeholders where the licensed media volunteer can paste official lyrics from CCLI SongSelect (e.g. Slide 1: [Verse 1 - Insert Licensed Lyrics], Slide 2: [Chorus - Insert Licensed Lyrics]).

TRANSLITERATION FEATURE:
- For songs in Indic scripts (Tamil, Malayalam, Telugu, Hindi) or other non-Latin scripts, generate an accurate, readable Latin-script transliteration for every lyric line.
- This allows diaspora youth and church attendees who speak the language but cannot read the script to participate.

PROOFREADING:
- Check slide lines for common church projection typos (e.g. "heavens" vs "hevens", incorrect capitalization of divine pronouns, punctuation).
- Provide notes as constructive recommendations for the media volunteer.
"""


async def build_slides_for_song(
    song: Song,
    custom_lyrics: Optional[str] = None
) -> SongPackResult:
    """
    Builds slides, performs proofreading, and generates transliteration for a single song.
    """
    is_pd = (song.verdict and song.verdict.legal_status == LegalStatus.PUBLIC_DOMAIN)

    prompt = f"""
    Build presentation slides for:
    - Song Index: {song.index}
    - Title: "{song.title}"
    - Artist / Author: "{song.artist_or_source}"
    - Language: "{song.language}"
    - Legal Status: "{song.verdict.legal_status.value if song.verdict else 'unknown'}"
    - Is Public Domain: {is_pd}
    - Custom Lyrics Provided by User: {f'"{custom_lyrics}"' if custom_lyrics else 'None'}

    Follow the strict Lyrics Policy:
    - If Public Domain or custom lyrics provided, format verses and choruses into 2-4 lines per slide.
    - If Copyrighted and no custom lyrics provided, provide labeled placeholders for SongSelect paste.
    - If the language uses an Indic or non-Latin script, include Latin transliteration for each line.
    """

    result = await generate_structured(
        prompt=prompt,
        schema=SongPackResult,
        system_instruction=PACK_SYSTEM_INSTRUCTION
    )
    return result


async def generate_pack_for_setlist(
    songs: List[Song],
    custom_lyrics_map: Optional[Dict[int, str]] = None
) -> List[Song]:
    """
    Populates slides for all songs in a setlist.
    """
    updated_songs = []
    custom_lyrics_map = custom_lyrics_map or {}

    for song in songs:
        custom_text = custom_lyrics_map.get(song.index)
        pack_res = await build_slides_for_song(song, custom_text)

        # Convert to domain Slide models
        domain_slides = [
            Slide(
                song_index=song.index,
                label=s.label,
                lines=s.lines,
                transliteration=s.transliteration
            )
            for s in pack_res.slides
        ]

        song.slides = domain_slides
        song.lyrics_policy = pack_res.lyrics_policy
        updated_songs.append(song)

    return updated_songs
