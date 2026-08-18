from datetime import datetime
from typing import Optional
from ..models import ServicePlan, CloseoutPack
from ..services.gemini_client import generate_structured
from pydantic import BaseModel, Field


class DisputeItem(BaseModel):
    song_title: str
    dispute_paragraph: str = Field(
        description="Formal, ready-to-paste paragraph explaining the church's license or public domain status with cited sources for YouTube dispute form"
    )


class GeneratedCloseoutDraft(BaseModel):
    service_summary: str = Field(description="Inspiring, calm 2-sentence summary for the YouTube description")
    disputes: list[DisputeItem] = Field(description="Dispute explanations for each song")


CLOSEOUT_SYSTEM_INSTRUCTION = """
You are Selah's Church Broadcast Close-Out Assistant.
Your task is to generate post-broadcast compliance documentation, including YouTube stream descriptions, CCLI usage logs, and Content ID dispute paragraphs.

DISPUTE WRITING GUIDANCE:
- For copyrighted songs covered by CCLI Streaming License: Cite the exact church license, song title, author, CCLI song ID, and note that the church holds non-commercial live streaming synchronization rights under CCLI.
- For public domain songs: State clearly that the musical composition and lyrics are in the Public Domain (published prior to 1929/1930) and that this live broadcast is an original church rendition, not a copyrighted master recording.
"""


def _format_seconds(seconds: int) -> str:
    """Format seconds into YouTube chapter timestamp e.g. 0:00 or 1:04:12"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


async def generate_closeout_pack(plan: ServicePlan) -> CloseoutPack:
    """
    Assembles the complete CloseoutPack including:
    1. YouTube description with mandatory CCLI attributions.
    2. YouTube chapter markers.
    3. CCLI usage log table.
    4. YouTube Content ID dispute kit.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Format Chapter Markers (Ensure first is 0:00)
    chapter_lines = []
    has_zero = False
    for ch in plan.chapters:
        ts = _format_seconds(ch.seconds_from_start)
        if ch.seconds_from_start == 0:
            has_zero = True
        chapter_lines.append(f"{ts} {ch.label}")

    if not has_zero:
        chapter_lines.insert(0, "0:00 Welcome & Opening")

    chapters_text = "\n".join(chapter_lines)

    # 2. Collect Attributions
    attributions = []
    for s in plan.songs:
        if s.verdict and s.verdict.attribution_line:
            attributions.append(s.verdict.attribution_line)
        else:
            attributions.append(f"{s.title} - {s.artist_or_source or 'Worship'}")

    licenses_str = ", ".join(plan.licenses_held) if plan.licenses_held else "None recorded"

    # 3. Use Gemini to draft dispute paragraphs and description blurb
    songs_context = []
    for s in plan.songs:
        v = s.verdict
        songs_context.append({
            "title": s.title,
            "artist": s.artist_or_source,
            "owner": v.owner if v else "Unknown",
            "ccli_number": v.ccli_number if v else "N/A",
            "legal_status": v.legal_status.value if v else "unknown",
            "sources": [src.model_dump() for src in (v.sources if v else [])]
        })

    prompt = f"""
    Generate the closeout pack details for:
    - Service Name: "{plan.service_name}"
    - Stream Title: "{plan.stream_title}"
    - Licenses Held: {licenses_str}
    - Songs: {songs_context}
    """

    ai_draft = await generate_structured(
        prompt=prompt,
        schema=GeneratedCloseoutDraft,
        system_instruction=CLOSEOUT_SYSTEM_INSTRUCTION
    )

    # 4. Build YouTube Description
    description_parts = [
        f"{plan.stream_title}",
        "",
        ai_draft.service_summary,
        "",
        "--- MUSIC COPYRIGHT & LICENSING ATTRIBUTION ---",
        "Songs used under church worship streaming licensing:",
    ]
    for attr in attributions:
        description_parts.append(f"• {attr}")

    description_parts.extend([
        "",
        f"Broadcast Licenses Held: {licenses_str}",
        "",
        "--- TIMESTAMPS / CHAPTERS ---",
        chapters_text,
        "",
        "Streamed live with Selah Telecast Copilot."
    ])
    youtube_description = "\n".join(description_parts)

    # 5. Build CCLI Usage Log
    ccli_log_lines = [
        "| Date | Song Title | Artist / Author | CCLI Number | Usage Type | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for s in plan.songs:
        ccli_num = s.verdict.ccli_number if s.verdict and s.verdict.ccli_number else "N/A"
        owner = s.verdict.owner if s.verdict and s.verdict.owner else (s.artist_or_source or "Traditional")
        status_val = s.verdict.legal_status.value if s.verdict else "reported"
        ccli_log_lines.append(f"| {today_str} | {s.title} | {owner} | {ccli_num} | Streamed Performance | {status_val} |")

    ccli_usage_log = "\n".join(ccli_log_lines)

    # 6. Build Dispute Pack
    dispute_parts = [
        "# YouTube Content ID Dispute Kit",
        f"Generated for: {plan.stream_title} ({today_str})",
        f"Licenses Held: {licenses_str}",
        "",
        "If your livestream receives a copyright claim or automated mute, copy the relevant statement below into YouTube's dispute form (Select 'I have permission / license to use this content'):",
        ""
    ]

    for item in ai_draft.disputes:
        dispute_parts.append(f"### Dispute Statement: {item.song_title}")
        dispute_parts.append(f"> {item.dispute_paragraph}")
        dispute_parts.append("")

    dispute_pack = "\n".join(dispute_parts)

    return CloseoutPack(
        plan_id=plan.id,
        youtube_description=youtube_description,
        ccli_usage_log=ccli_usage_log,
        chapters_text=chapters_text,
        dispute_pack=dispute_pack
    )


def generate_closeout_markdown_document(pack: CloseoutPack, plan: ServicePlan) -> str:
    """
    Returns the complete closeout pack as a single downloadable markdown file.
    """
    return f"""# Selah Broadcast Close-Out Pack
**Service:** {plan.service_name}  
**Stream Title:** {plan.stream_title}  
**Date:** {datetime.now().strftime("%B %d, %Y")}  
**Licenses Held:** {', '.join(plan.licenses_held) if plan.licenses_held else 'None recorded'}

---

## 1. YouTube Video Description (Copy & Paste)
```
{pack.youtube_description}
```

---

## 2. YouTube Chapters
```
{pack.chapters_text}
```

---

## 3. CCLI Usage Log (For Reporting Portal)
{pack.ccli_usage_log}

---

## 4. YouTube Content ID Dispute Pack
{pack.dispute_pack}

---
*Generated by Selah — The Live Telecast Copilot for Church Media Volunteers.*
"""
