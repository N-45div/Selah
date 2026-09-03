import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from ..models import SongVerdict, LegalStatus, ContentIdRisk, Source
from ..services.parallel_client import search_licensing_web, async_research_licensing_deep
from ..services.gemini_client import generate_structured, next_api_key
from ..config import GEMINI_MODEL


LICENSING_AGENT_INSTRUCTION = """
You are Selah's Autonomous Licensing & Broadcast Rights Research Agent.
Your mission is to perform deep musicological and legal research for worship songs and hymns to protect live church telecasts from audio muting, copyright strikes, and statutory penalties.

CRITICAL OPERATIONAL RULES:
1. NEVER suggest, recommend, or substitute songs. Selah never dictates worship choices. It gives the human operator clear operational choices (e.g., mute livestream audio, verify CCLI Streaming coverage, obtain synchronization license).
2. For every song, determine:
   - `legal_status`:
     * 'public_domain': Written before 1929 or authentic historic traditional hymn.
     * 'covered': Covered by the church's declared licenses (e.g. CCLI Streaming License).
     * 'needs_license': Copyrighted and NOT covered by in-person-only or basic licenses without streaming addon.
     * 'unknown': Unable to confirm ownership with high confidence.
   - `ccli_number`: Look up the exact CCLI SongSelect ID (e.g., 3350395 for 'In Christ Alone', 7115744 for 'Way Maker').
   - `content_id_risk`: 'low' (public domain), 'medium' (covered with attribution required), or 'high' (strictly claimed by major labels like Capitol CMG / Sony / Bethel Music).
   - `options`: 2-4 concrete actions for the human volunteer (e.g. 'Mute stream audio during song', 'Acquire CCLI Streaming Plus License for multitracks', 'Verify arrangement year').
   - `sources`: Provide verifiable primary sources (CCLI SongSelect, Hymnary.org, Capitol CMG, Easy Song, etc.) with URL and title.
   - `attribution_line`: A clean, ready-to-paste video description attribution string.
"""


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if "```json" in cleaned:
        match = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
    elif "```" in cleaned:
        match = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)
    return cleaned.strip()


async def research_song(
    title: str,
    artist_or_source: str,
    licenses_held: List[str],
    language: str = "English"
) -> SongVerdict:
    """
    Autonomous research agent combining Google ADK runner with Parallel Search,
    with direct Parallel deep-search fallback for resilience.
    Rotates process-global GOOGLE_API_KEY from project pool before each ADK run.
    """
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
    max_retries = 4

    for attempt in range(max_retries):
        # Rotate key from the project pool BEFORE constructing the agent/runner
        try:
            current_key = next_api_key()
            os.environ["GOOGLE_API_KEY"] = current_key
        except Exception as e:
            print(f"Key rotation notice: {e}")

        agent = Agent(
            name="LicensingAgent",
            model=GEMINI_MODEL,
            description="Autonomous copyright research agent using Parallel Search tool",
            instruction=LICENSING_AGENT_INSTRUCTION,
            tools=[search_licensing_web]
        )
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
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str:
                # Parse retryDelay from Google API response if available
                delay_match = re.search(r"retryDelay[\"']?\s*:\s*[\"']?(\d+(?:\.\d+)?)s?", err_str)
                if delay_match:
                    wait_time = float(delay_match.group(1)) + 1.0
                else:
                    wait_time = 35.0 + (attempt * 5.0)
                print(f"[ADK Rate/RPM Notice] Rotating key pool & backing off {wait_time:.1f}s on '{title}' (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    print(f"ADK runner notice on '{title}': {e}")
                await asyncio.sleep(2.0)
        finally:
            try:
                await runner.close()
            except Exception:
                pass

    # Direct Parallel Search Grounding Fallback if ADK returned empty
    if not final_text:
        print(f"Executing direct Parallel deep search grounding fallback for '{title}'...")
        deep_search = await async_research_licensing_deep(title, artist_or_source, licenses_held)
        search_results = deep_search.get("results", [])
        
        extracted_sources: List[Source] = []
        ccli_found = None
        for item in search_results[:4]:
            t = getattr(item, "title", "Citation") or "Citation"
            u = getattr(item, "url", "") or ""
            if "ccli.com/songs/" in u:
                m = re.search(r"ccli\.com/songs/(\d+)", u)
                if m:
                    ccli_found = m.group(1)
            extracted_sources.append(Source(url=u, title=t, note="Direct Parallel Web verification"))

        fallback_prompt = f"""
        Generate a structured SongVerdict for '{title}' by '{artist_or_source}' based on these Parallel search findings:
        - Church Licenses: {json.dumps(licenses_held)}
        - Detected CCLI ID: {ccli_found}
        - Search Citations: {[s.model_dump() for s in extracted_sources]}
        """
        try:
            return await generate_structured(
                prompt=fallback_prompt,
                schema=SongVerdict,
                system_instruction=LICENSING_AGENT_INSTRUCTION
            )
        except Exception as deep_err:
            print(f"Deep search structured synthesis notice: {deep_err}")

    # Attempt to parse ADK JSON
    cleaned = _clean_json_text(final_text)
    try:
        data = json.loads(cleaned)
        return SongVerdict(**data)
    except Exception as parse_err:
        print(f"Direct JSON parse failed for '{title}': {parse_err}. Initiating repair pass...")

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
            print(f"Repair pass notice for '{title}': {repair_err}")
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
    Research all songs sequentially with rate limiting.
    """
    results = []
    for item in songs_data:
        verdict = await research_song(
            title=item.get("title", ""),
            artist_or_source=item.get("artist_or_source", ""),
            licenses_held=licenses_held,
            language=item.get("language", "English")
        )
        results.append(verdict)
        await asyncio.sleep(2)
    return results
