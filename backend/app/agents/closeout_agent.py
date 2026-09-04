from datetime import datetime
from typing import Optional, List
from ..models import ServicePlan, CloseoutPack, LegalStatus
from ..services.gemini_client import generate_structured
from pydantic import BaseModel, Field


class DisputeItem(BaseModel):
    song_title: str
    youtube_dispute: str = Field(
        description="Ready-to-paste dispute statement. Cite an active streaming licence ONLY if one is listed in Licenses Held and the song's legal_status is 'covered'; for public_domain cite public domain only."
    )
    facebook_dispute: str = Field(
        description="Concise statement for Meta / Facebook Rights Manager appeal"
    )


class GeneratedCloseoutDraft(BaseModel):
    service_summary: str = Field(description="Inspiring, calm 2-sentence summary for the YouTube description")
    disputes: List[DisputeItem] = Field(description="Dispute explanations for each song")


CLOSEOUT_SYSTEM_INSTRUCTION = """
You are Selah's Church Broadcast Close-Out Assistant.
Your task is to generate post-broadcast compliance documentation across platforms (YouTube, Facebook Live, Twitch), including YouTube stream descriptions, CCLI usage logs, and multi-platform Content ID dispute statements.

DISPUTE DRAFTING GUIDELINES:
1. YouTube Content ID:
   - For copyrighted songs covered by an active streaming licence: Cite the church's streaming licence, registered publisher, CCLI Song ID, and note that the church holds non-commercial live streaming synchronization rights under its licence agreement. Never cite 17 U.S.C. § 106 and never argue fair use under § 107.
   - For public domain songs: State clearly that the musical composition and lyrics are in the Public Domain (cite publication_year if provided, or first published 1930 or earlier in the US) and that this live broadcast is an original rendition, not a copyrighted master recording.
2. Facebook / Meta Rights Manager:
   - Provide a concise statement citing the active church streaming licence covering this live telecast.
3. STRICT COMPLIANCE RULE:
   - If a song's legal_status is not 'covered' or 'public_domain', or if no streaming licence is listed in Licenses Held, you MUST NOT state that the church holds any streaming licence. Output: "DO NOT FILE — Selah could not confirm streaming coverage for '{song_title}'. Filing a dispute would assert a licence you may not hold. Confirm coverage with your licensing administrator."
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
    Assembles the complete Multi-Platform CloseoutPack including:
    1. YouTube description with mandatory CCLI attributions.
    2. YouTube chapter markers.
    3. CCLI usage log table for quarterly reporting.
    4. Multi-Platform Content ID & Rights Manager dispute kit.
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
        chapter_lines.insert(0, "0:00 Welcome & Opening Worship")

    chapters_text = "\n".join(chapter_lines)

    # 2. Collect Attributions
    attributions = []
    for s in plan.songs:
        if s.verdict and s.verdict.attribution_line:
            attributions.append(s.verdict.attribution_line)
        else:
            ccli = f" (CCLI #{s.verdict.ccli_number})" if s.verdict and s.verdict.ccli_number else ""
            attributions.append(f"{s.title} - {s.artist_or_source or 'Traditional'}{ccli}")

    # Derive held streaming licenses
    held_streaming = [l for l in plan.licenses_held if "streaming" in l.lower() or "onelicense" in l.lower()]
    held_streaming_str = ", ".join(held_streaming) if held_streaming else "None"
    all_licenses_str = ", ".join(plan.licenses_held) if plan.licenses_held else "None recorded"

    def _is_covered(s) -> bool:
        return bool(held_streaming) and s.verdict is not None and s.verdict.legal_status == LegalStatus.COVERED

    # 3. Use Gemini to draft dispute paragraphs and description blurb
    songs_context = []
    for s in plan.songs:
        v = s.verdict
        songs_context.append({
            "title": s.title,
            "artist": s.artist_or_source,
            "owner": v.owner if v else "Unknown",
            "publication_year": v.publication_year if v else None,
            "ccli_number": v.ccli_number if v else "N/A",
            "legal_status": v.legal_status.value if v else "unknown",
            "sources": [src.model_dump() for src in (v.sources if v else [])]
        })

    prompt = f"""
    Generate the closeout pack details for:
    - Service Name: "{plan.service_name}"
    - Stream Title: "{plan.stream_title}"
    - Verified Streaming Licenses Held: {held_streaming_str}
    - Songs: {songs_context}
    """

    try:
        ai_draft = await generate_structured(
            prompt=prompt,
            schema=GeneratedCloseoutDraft,
            system_instruction=CLOSEOUT_SYSTEM_INSTRUCTION
        )
    except Exception as e:
        print(f"Closeout AI drafting fallback notice: {e}")
        # Deterministic fallback
        fallback_disputes = []
        for s in plan.songs:
            ccli_id = s.verdict.ccli_number if s.verdict and s.verdict.ccli_number else "Registered"
            owner_name = s.verdict.owner if s.verdict and s.verdict.owner else "Copyright Owner"
            is_pd = s.verdict and s.verdict.legal_status == LegalStatus.PUBLIC_DOMAIN
            if is_pd:
                pub_year = s.verdict.publication_year if (s.verdict and s.verdict.publication_year) else None
                year_clause = f"first published {pub_year} (1930 or earlier)" if pub_year else "first published 1930 or earlier in the US"
                yt_disp = f"The composition and lyrics of '{s.title}' are in the Public Domain ({year_clause}). This broadcast is an original live church performance and does not infringe any sound recording copyright."
                fb_disp = f"Public Domain hymn '{s.title}' ({year_clause}) performed live by church congregation. No master recording copyright applies."
            elif _is_covered(s):
                yt_disp = f"This church holds an active streaming licence ({held_streaming_str}) covering '{s.title}' (CCLI SongSelect #{ccli_id}, Administered by {owner_name}). This is a live performance during a non-commercial religious service."
                fb_disp = f"Covered under active church streaming licence ({held_streaming_str}) for '{s.title}' (CCLI #{ccli_id})."
            else:
                status_label = s.verdict.legal_status.value if s.verdict else 'unresearched'
                yt_disp = f"DO NOT FILE — Selah could not confirm streaming coverage for '{s.title}' (status: {status_label}). Filing a dispute would assert a licence you may not hold. Confirm coverage with your licensing administrator before responding to any claim."
                fb_disp = yt_disp
            fallback_disputes.append(DisputeItem(song_title=s.title, youtube_dispute=yt_disp, facebook_dispute=fb_disp))

        ai_draft = GeneratedCloseoutDraft(
            service_summary=f"Sunday live broadcast of {plan.service_name}. Join us for worship and the Word.",
            disputes=fallback_disputes
        )

    # Deterministically enforce compliance on AI draft
    clean_disputes = []
    by_title = {d.song_title.strip().lower(): d for d in (ai_draft.disputes or [])}
    for s in plan.songs:
        s_title_key = s.title.strip().lower()
        existing_disp = by_title.get(s_title_key)
        is_pd = s.verdict and s.verdict.legal_status == LegalStatus.PUBLIC_DOMAIN
        if is_pd and existing_disp and "do not file" not in existing_disp.youtube_dispute.lower():
            clean_disputes.append(existing_disp)
        elif _is_covered(s) and existing_disp and "do not file" not in existing_disp.youtube_dispute.lower():
            clean_disputes.append(existing_disp)
        else:
            status_label = s.verdict.legal_status.value if s.verdict else 'unresearched'
            safe_yt = f"DO NOT FILE — Selah could not confirm streaming coverage for '{s.title}' (status: {status_label}). Filing a dispute would assert a licence you may not hold. Confirm coverage with your licensing administrator before responding to any claim."
            clean_disputes.append(DisputeItem(song_title=s.title, youtube_dispute=safe_yt, facebook_dispute=safe_yt))
    ai_draft.disputes = clean_disputes

    # 4. Build YouTube Description
    description_header = (
        "Songs broadcast under church worship streaming licensing agreements:"
        if held_streaming
        else "Songs performed during church worship service:"
    )
    description_parts = [
        f"{plan.stream_title}",
        "",
        ai_draft.service_summary,
        "",
        "--- MUSIC COPYRIGHT & LICENSING ATTRIBUTION ---",
        description_header,
    ]
    for attr in attributions:
        description_parts.append(f"• {attr}")

    if plan.licenses_held:
        description_parts.extend([
            "",
            f"Broadcast Licenses Held: {all_licenses_str}"
        ])

    description_parts.extend([
        "",
        "--- TIMESTAMPS / CHAPTERS ---",
        chapters_text,
        "",
        "Streamed live with Selah Telecast Copilot."
    ])
    youtube_description = "\n".join(description_parts)

    # 5. Build CCLI Usage Log
    ccli_log_lines = [
        "| Date | Song Title | Artist / Owner | CCLI Number | Usage Type | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for s in plan.songs:
        ccli_num = s.verdict.ccli_number if s.verdict and s.verdict.ccli_number else "N/A"
        owner = s.verdict.owner if s.verdict and s.verdict.owner else (s.artist_or_source or "Traditional")
        is_pd = s.verdict and s.verdict.legal_status == LegalStatus.PUBLIC_DOMAIN
        
        if s.resolution and "mute" in s.resolution.lower():
            usage_type = "Muted during stream — not broadcast"
        elif is_pd:
            usage_type = "Public domain — not reportable under CCLI"
        else:
            usage_type = "Streamed Live Performance"

        if s.verdict:
            status_map = {
                LegalStatus.COVERED: "Covered by streaming licence",
                LegalStatus.PUBLIC_DOMAIN: "Public Domain",
                LegalStatus.NEEDS_LICENSE: "NOT CLEARED — needs licence",
                LegalStatus.UNKNOWN: "Unverified — manual check"
            }
            status_val = status_map.get(s.verdict.legal_status, s.verdict.legal_status.value)
        else:
            status_val = "Unresearched"

        ccli_log_lines.append(f"| {today_str} | {s.title} | {owner} | {ccli_num} | {usage_type} | {status_val} |")

    ccli_usage_log = "\n".join(ccli_log_lines)

    # 6. Build Content ID Dispute Statements
    dispute_parts = [
        "# Content ID Dispute Statements (draft — review before filing)",
        f"Generated for: {plan.stream_title} ({today_str})",
        f"Licenses Held: {all_licenses_str}",
        ""
    ]

    if not held_streaming:
        dispute_parts.extend([
            "> ⚠️ NOTICE: No streaming license (e.g. CCLI Streaming License) is recorded for this broadcast. Do NOT file dispute claims asserting licensing coverage until verified with your church administrator.",
            ""
        ])

    dispute_parts.extend([
        "If your broadcast receives an automated Content ID mute or claim, copy the relevant statement into the platform dispute portal after reviewing:",
        ""
    ])

    for item in ai_draft.disputes:
        dispute_parts.append(f"## {item.song_title}")
        dispute_parts.append(f"**YouTube Content ID Dispute:**")
        dispute_parts.append(f"> {item.youtube_dispute}")
        dispute_parts.append("")
        dispute_parts.append(f"**Facebook / Meta Rights Manager Appeal:**")
        dispute_parts.append(f"> {item.facebook_dispute}")
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

## 2. Timestamped Chapters
```
{pack.chapters_text}
```

---

## 3. CCLI Quarterly Reporting Log
{pack.ccli_usage_log}

---

## 4. Content ID Dispute Statements (drafts)
{pack.dispute_pack}

---
*Generated by Selah Telecast Copilot — Live Church Broadcast Compliance Engine*
"""
