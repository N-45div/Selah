import re
from typing import List, Optional
from pydantic import BaseModel, Field
from google.genai import types
from ..services.gemini_client import generate_structured
from ..models import Song


class ExtractedSongItem(BaseModel):
    title: str = Field(description="The recognizable title of the hymn or worship song")
    artist_or_source: str = Field(default="", description="Artist, author, band, or hymnal source mentioned")
    language: str = Field(default="English", description="Primary language of the song (e.g. English, Tamil, Hindi, Spanish)")
    is_illegible: bool = Field(default=False, description="Flag true if handwritten text was partially illegible or uncertain")
    is_medley_child: bool = Field(default=False, description="Flag true if this song was split from a compound medley")
    medley_parent_title: Optional[str] = Field(default=None, description="Original compound line if part of a medley")


class ExtractedSetlist(BaseModel):
    service_name: Optional[str] = Field(default="Sunday Worship Service", description="Extracted or inferred service title")
    songs: List[ExtractedSongItem] = Field(description="List of songs extracted in exact order")


SETLIST_SYSTEM_INSTRUCTION = """
You are Selah's Setlist Parser, an expert assistant for church media teams.
Your job is to parse handwritten notes, bulleted lists, WhatsApp messages, or order-of-worship sheets into an ordered list of worship songs and hymns.

CRITICAL RULES:
1. NEVER invent, recommend, or substitute songs. Extract only what is written or visible.
2. MEDLEY DECOMPOSITION (CRITICAL):
   - If a line contains compound songs separated by '/', '->', '-->', '+', or 'medley' (e.g. "Way Maker / Great Are You Lord" or "10,000 Reasons -> Goodness of God"), SPLIT them into separate sequential song items.
   - Mark `is_medley_child: true` and record the original string in `medley_parent_title`.
3. If text is ambiguous or partially illegible, flag `is_illegible: true` and provide your closest transcription for the human to review.
4. Detect the primary language (e.g., English, Tamil, Malayalam, Hindi, Telugu, Spanish, etc.).
5. Separate the song title from artist/writer credits (e.g., "10,000 Reasons - Matt Redman" -> title: "10,000 Reasons", artist: "Matt Redman").
"""


def _split_compound_line_fallback(title: str, artist: str, language: str) -> List[ExtractedSongItem]:
    """
    Fallback regex splitter for compound medley lines separated by delimiters.
    """
    delimiters = [r"\s*/\s*", r"\s*->\s*", r"\s*-->\s*", r"\s*\+\s*", r"\s*\|\s*"]
    combined_pattern = "|".join(delimiters)
    parts = re.split(combined_pattern, title)
    if len(parts) > 1:
        items = []
        for p in parts:
            cleaned = p.strip()
            if cleaned:
                items.append(ExtractedSongItem(
                    title=cleaned,
                    artist_or_source=artist,
                    language=language,
                    is_medley_child=True,
                    medley_parent_title=title
                ))
        return items
    return [ExtractedSongItem(title=title, artist_or_source=artist, language=language)]


async def parse_setlist_text(text: str) -> ExtractedSetlist:
    """
    Parses raw pasted text / WhatsApp message into structured setlist with medley decomposition.
    """
    prompt = f"Please extract all worship songs and hymns from this setlist text. Decompose any compound medleys into individual songs:\n\n{text}"
    result = await generate_structured(
        prompt=prompt,
        schema=ExtractedSetlist,
        system_instruction=SETLIST_SYSTEM_INSTRUCTION
    )

    # Post-process fallback for any un-split medley delimiters
    expanded_songs: List[ExtractedSongItem] = []
    for item in result.songs:
        if not item.is_medley_child and any(delim in item.title for delim in ("/", "->", "-->", " + ")):
            expanded_songs.extend(_split_compound_line_fallback(item.title, item.artist_or_source, item.language))
        else:
            expanded_songs.append(item)

    result.songs = expanded_songs
    return result


async def parse_setlist_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> ExtractedSetlist:
    """
    Multimodal parse of a handwritten or printed setlist photo.
    """
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type
    )

    prompt_content = [
        image_part,
        "Please carefully read this handwritten or printed set list image and extract each worship song/hymn in order. Decompose any compound medleys into separate songs. Do not invent any songs."
    ]

    result = await generate_structured(
        prompt=prompt_content,
        schema=ExtractedSetlist,
        system_instruction=SETLIST_SYSTEM_INSTRUCTION
    )
    return result


def convert_extracted_to_songs(extracted: ExtractedSetlist) -> List[Song]:
    """
    Converts extracted items into initialized Song domain models with pending research status.
    """
    songs = []
    for idx, item in enumerate(extracted.songs):
        title = item.title.strip()
        if item.is_illegible:
            title = f"{title} (Needs verification)"
        if item.is_medley_child:
            title = f"{title} [Medley]"

        songs.append(Song(
            index=idx,
            title=title,
            artist_or_source=item.artist_or_source.strip(),
            language=item.language.strip() or "English",
            research_status="pending",
            verdict=None,
            resolution=None,
            slides=[],
            lyrics_policy="full"
        ))
    return songs
