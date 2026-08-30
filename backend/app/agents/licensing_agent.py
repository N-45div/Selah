import json
import re
import asyncio
from typing import List, Optional, Dict, Any
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from ..config import GEMINI_MODEL
from ..models import SongVerdict, LegalStatus, ContentIdRisk, Source
from ..services.parallel_client import search_licensing_web
from ..services.gemini_client import generate_structured


LICENSING_AGENT_INSTRUCTION = """
You are Selah's Music Licensing & Copyright Research Agent for live church broadcasts.
Your mission is to perform thorough, evidence-based copyright and YouTube Content ID risk research on worship songs and hymns.

YOUR RESEARCH TOOL:
You have access to `search_licensing_web(objective: str, search_queries: list[str])`.
All web research is powered by Parallel Search. Always provide 1-3 targeted 3-6 word search queries per search step.

DOMAIN RULES & GOTCHAS (CRITICAL):
1. PUBLIC DOMAIN VS MODERN ARRANGEMENTS:
   - Traditional hymn text (e.g. John Newton's "Amazing Grace", Horatio Spafford's "It Is Well") is Public Domain.
   - BUT modern arrangements, added refrains, or contemporary retunes (e.g., Chris Tomlin's "Amazing Grace (My Chains Are Gone)") are fully copyrighted!
   - Modern hymns written after 1930 (e.g., Keith Getty & Stuart Townend's "In Christ Alone") are fully copyrighted by publishers like Thankyou Music / Capitol CMG.

2. CCLI LICENSING TIERS:
   - Check if the song is in the CCLI SongSelect catalog and locate its exact CCLI song number.
   - The basic "CCLI Copyright License" covers in-person projection/reproduction ONLY — it DOES NOT cover streaming/broadcasting!
   - Streaming requires the "CCLI Streaming License" or "CCLI Streaming Plus License" (for multitracks/master recordings) or OneLicense (for specific liturgical publishers).
   - Evaluate `legal_status` as `covered` ONLY if the church's provided `licenses_held` covers online streaming for this song. If the church only holds a basic in-person license, mark `needs_license`.

3. YOUTUBE CONTENT ID AXIS:
   - YouTube Content ID operates independently of church licensing. A church can hold all CCLI licenses and STILL receive an automated Content ID mute or copyright claim!
   - Commercial worship tracks (e.g., Elevation Worship, Hillsong, Bethel) or popular melodies have high Content ID risk.
   - Traditional hymns in public domain have medium risk (due to algorithms matching recorded performances).
   - Always provide clear dispute advice in `content_id_summary` (e.g. "Church holds streaming rights; dispute claim citing CCLI # / PD status").

4. HUMAN ACTION OPTIONS (NEVER SUBSTITUTE SONGS):
   - You MUST NEVER suggest alternative songs or replacement hymns.
   - The options list must provide practical operational choices for the church team (e.g., "Mute livestream audio during this song", "Confirm CCLI Streaming License tier", "Display CCLI copyright notice", "File YouTube Content ID dispute if flagged").

OUTPUT FORMAT:
Your final answer MUST be valid JSON (and ONLY JSON) matching this exact schema:
{
  "legal_status": "public_domain" | "covered" | "needs_license" | "unknown",
  "legal_summary": "2-3 plain sentences explaining the legal status to a church volunteer.",
  "content_id_risk": "low" | "medium" | "high",
  "content_id_summary": "Explanation of YouTube Content ID claim likelihood and clear dispute guidance.",
  "owner": "Copyright owner/publisher (e.g. Thankyou Music / Capitol CMG / Public Domain)",
  "ccli_number": "CCLI song number (e.g. 3350395) or null",
  "options": ["Option 1", "Option 2"],
  "sources": [
    {
      "url": "https://...",
      "title": "Page Title",
      "note": "One sentence explaining what this source proves"
    }
  ],
  "attribution_line": "Ready-to-paste attribution for video description (e.g. In Christ Alone - Keith Getty, Stuart Townend © 2001 Thankyou Music / CCLI #3350395)"
}
"""


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences and extraneous leading/trailing text."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


async def research_song(
    title: str,
    artist_or_source: str,
    licenses_held: List[str],
    language: str = "English"
) -> SongVerdict:
    """
    Executes an ADK Agent with the Parallel Search tool to research a song's licensing status and Content ID risk.
    """
    # Initialize the ADK Agent
    agent = Agent(
        name=f"LicensingAgent_{abs(hash(title)) % 10000}",
        model=GEMINI_MODEL,
        description="Church music licensing and YouTube Content ID research specialist.",
        instruction=LICENSING_AGENT_INSTRUCTION,
        tools=[search_licensing_web]
    )

    request_prompt = f"""
    Please research the following worship song/hymn:
    - Song Title: "{title}"
    - Artist / Author / Source: "{artist_or_source}"
    - Primary Language: {language}
    - Licenses Held by Church: {json.dumps(licenses_held)}

    Perform necessary web searches via Parallel Search to identify:
    1. Writer(s), publication year, and current copyright owner/administrator or Public Domain status.
    2. CCLI SongSelect ID number and licensing requirements.
    3. YouTube Content ID risk profile and mitigation/dispute wording.
    4. Provide full source citations with URLs and titles.

    Output STRICT JSON matching the SongVerdict schema.
    """

    final_text = ""
    max_retries = 3

    for attempt in range(max_retries):
        runner = InMemoryRunner(agent=agent)
        try:
            events = await runner.run_debug(request_prompt, quiet=True)
            for event in reversed(events):
                if hasattr(event, "content") and event.content:
                    parts = getattr(event.content, "parts", [])
                    for part in parts:
                        if hasattr(part, "text") and part.text:
                            final_text = part.text
                            break
                if final_text:
                    break
            if final_text:
                break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 15.0 * (attempt + 1)
                print(f"[ADK 429 Rate Limit] Backing off for {wait_time}s on '{title}'...")
                await asyncio.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    print(f"ADK runner error on '{title}': {e}")
                await asyncio.sleep(3.0)
        finally:
            try:
                await runner.close()
            except Exception:
                pass


    # Attempt to parse JSON
    cleaned = _clean_json_text(final_text)
    try:
        data = json.loads(cleaned)
        return SongVerdict(**data)
    except Exception as parse_err:
        print(f"Direct JSON parse failed for '{title}': {parse_err}. Initiating repair pass...")

        # Repair pass via structured Gemini call
        repair_prompt = f"""
        Convert the following research findings into the exact SongVerdict JSON schema.
        Do not invent new facts. Maintain all sources and details accurately:

        RAW RESEARCH TEXT:
        {final_text if final_text else 'No raw text gathered.'}
        """

        try:
            repaired = await generate_structured(
                prompt=repair_prompt,
                schema=SongVerdict,
                system_instruction="You are a JSON formatting assistant. Convert verbatim into the schema without inventing facts."
            )
            return repaired
        except Exception as repair_err:
            print(f"Repair pass failed for '{title}': {repair_err}")
            # Safe fallback verdict
            return SongVerdict(
                legal_status=LegalStatus.UNKNOWN,
                legal_summary=f"Unable to automatically confirm licensing details for '{title}'. Please verify in CCLI SongSelect.",
                content_id_risk=ContentIdRisk.MEDIUM,
                content_id_summary="Moderate Content ID risk. If streamed, keep documentation ready for YouTube dispute.",
                owner=artist_or_source or "Unknown",
                ccli_number=None,
                options=[
                    "Check CCLI SongSelect manually for license coverage",
                    "Mute livestream audio during this song",
                    "Confirm performance rights coverage with worship leader"
                ],
                sources=[],
                attribution_line=f"{title} - {artist_or_source or 'Traditional'}"
            )


async def research_setlist_concurrently(
    songs_data: List[Dict[str, Any]],
    licenses_held: List[str]
) -> List[SongVerdict]:
    """
    Runs licensing research for all songs concurrently using asyncio.gather.
    """
    tasks = [
        research_song(
            title=song["title"],
            artist_or_source=song.get("artist_or_source", ""),
            licenses_held=licenses_held,
            language=song.get("language", "English")
        )
        for song in songs_data
    ]
    return await asyncio.gather(*tasks, return_exceptions=False)
