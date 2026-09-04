import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from ..models import SongVerdict, LegalStatus, ContentIdRisk, Source
from ..services.parallel_client import search_licensing_web, async_research_licensing_deep, PARALLEL_URLS, _clean_text
from ..services.gemini_client import generate_structured, next_api_key
from ..config import GEMINI_MODEL


LICENSING_AGENT_INSTRUCTION = """
You are Selah's Autonomous Licensing & Broadcast Rights Research Agent.
Your mission is to perform deep musicological and legal research for worship songs and hymns to protect live church telecasts from audio muting, copyright strikes, and statutory penalties.

CRITICAL OPERATIONAL RULES:
1. NEVER suggest, recommend, or substitute songs. Selah never dictates worship choices. It gives the human operator clear operational choices (e.g., mute livestream audio, verify CCLI Streaming coverage, obtain synchronization license).
2. For every song, determine:
   - `legal_status`:
     * 'public_domain': ONLY when BOTH the underlying composition/text AND the specific arrangement the church will perform are out of copyright. Pre-1930 hymn text set to a modern tune, or with an added modern refrain/bridge, is a copyrighted derivative work under 17 U.S.C. 103 (e.g. 'Amazing Grace (My Chains Are Gone)' CCLI 4768151; 'It Is Well' - Kristene DiMarco, CCLI 7021972; 'Holy Holy Holy (God With Us)' - Matt Maher). If the setlist gives no artist, or you cannot identify WHICH arrangement is being performed, return 'unknown' and include the option 'Confirm with the worship leader which arrangement the team is playing'. Never infer public domain from the title alone.
     * 'covered': Covered by the church's declared licenses (e.g. CCLI Streaming License).
     * 'needs_license': Copyrighted and NOT covered by in-person-only or basic licenses without streaming addon.
     * 'unknown': Unable to confirm ownership or arrangement with high confidence.
   - `ccli_number`: Look up the exact CCLI SongSelect ID (e.g., 3350395 for 'In Christ Alone', 7115744 for 'Way Maker').
   - `publication_year`: Integer original publication year if known/found (e.g. 1873, 1923). Essential for verifying Public Domain status (must be 1930 or earlier).
   - `content_id_risk`: 'low' (verified-PD arrangement performed live with no commercial master involved; a modern retune of a PD hymn is 'high' regardless of hymn age), 'medium' (covered live congregational performance), or 'high' (strictly claimed by major labels like Capitol CMG / Sony / Bethel Music).
   - `options`: 2-4 concrete operational actions for the human volunteer (e.g. 'Mute stream audio during song', 'Acquire CCLI Streaming Plus License for multitracks', 'Verify arrangement with worship lead').
   - `sources`: Provide verifiable primary sources (CCLI SongSelect, Hymnary.org, Capitol CMG, Easy Song, etc.) with URL and title.
   - `attribution_line`: A clean, ready-to-paste video description attribution string.
3. GROUNDING IS MANDATORY. If search_licensing_web returns an 'error' key or an empty 'results' list, you MUST NOT answer from memory: set legal_status='unknown', content_id_risk='high', sources=[], and state in legal_summary that the web verification step failed.
"""


def _unverified_verdict(title: str, artist_or_source: str, sources: Optional[List[Source]] = None) -> SongVerdict:
    return SongVerdict(
        legal_status=LegalStatus.UNKNOWN,
        legal_summary=f"Automated rights verification failed or was inconclusive for '{title}'. No reliable research evidence was confirmed. Please verify manually in CCLI SongSelect before broadcast.",
        content_id_risk=ContentIdRisk.HIGH,
        content_id_summary="Content ID risk was not assessed or web evidence was insufficient. Treat as high risk until manually confirmed.",
        owner=artist_or_source or "Unknown",
        ccli_number=None,
        options=[
            "Check CCLI SongSelect manually for license coverage",
            "Mute livestream audio during this song",
            "Confirm performance rights coverage with worship leader"
        ],
        sources=sources or [],
        attribution_line=f"{title} - {artist_or_source or 'Traditional'}"
    )


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
    token = PARALLEL_URLS.set(set())

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
                if getattr(event, "error_code", None):
                    print(f"[ADK error event] {event.error_code}: {getattr(event, 'error_message', '')}")
                    continue
                if not getattr(event, "is_final_response", lambda: True)():
                    continue
                if not (getattr(event, "content", None) and getattr(event.content, "parts", None)):
                    continue
                text = "".join(
                    getattr(p, "text", "") for p in event.content.parts
                    if getattr(p, "text", None) and not getattr(p, "thought", False)
                )
                if text.strip():
                    final_text = text
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

        if not search_results:
            print(f"Parallel returned no results for '{title}' - returning unverified verdict")
            return _unverified_verdict(title, artist_or_source)

        extracted_sources: List[Source] = []
        ccli_found = None
        for item in search_results[:4]:
            t = _clean_text(getattr(item, "title", "Citation") or "Citation")
            u = getattr(item, "url", "") or ""
            if "ccli.com/songs/" in u:
                m = re.search(r"ccli\.com/songs/(\d+)", u)
                if m:
                    ccli_found = m.group(1)
            extracted_sources.append(Source(url=u, title=t, note="Direct Parallel Web verification"))

        evidence = deep_search.get("evidence", "")
        fallback_prompt = f"""
        Generate a structured SongVerdict for '{title}' by '{artist_or_source}' based on these Parallel search findings:
        - Church Licenses: {json.dumps(licenses_held)}
        - Detected CCLI ID: {ccli_found}
        - Search Citations: {[s.model_dump() for s in extracted_sources]}

        WEB EVIDENCE (authoritative — prefer these facts over anything you recall; if they conflict with your memory, the evidence wins):
        {evidence if evidence else "(no web evidence retrieved)"}

        If the evidence does not establish the current copyright owner or streaming coverage, return legal_status='unknown' rather than guessing. Never suggest or substitute songs; options must be operational actions only.
        """
        try:
            verdict = await generate_structured(
                prompt=fallback_prompt,
                schema=SongVerdict,
                system_instruction=LICENSING_AGENT_INSTRUCTION
            )
            verdict.sources = extracted_sources
            return verdict
        except Exception as deep_err:
            print(f"Deep search structured synthesis notice: {deep_err}")
            return _unverified_verdict(title, artist_or_source, extracted_sources)

    # Attempt to parse ADK JSON
    if not final_text.strip():
        return _unverified_verdict(title, artist_or_source)

    cleaned = _clean_json_text(final_text)
    try:
        data = json.loads(cleaned)
        verdict = SongVerdict(**data)
    except Exception as parse_err:
        print(f"Direct JSON parse failed for '{title}': {parse_err}. Initiating repair pass...")
        if not final_text.strip():
            return _unverified_verdict(title, artist_or_source)

        repair_prompt = f"""
        Convert the following research findings into the exact SongVerdict JSON schema.
        Do not invent new facts. Maintain all sources and details accurately:

        RAW RESEARCH TEXT:
        {final_text}
        """

        try:
            verdict = await generate_structured(
                prompt=repair_prompt,
                schema=SongVerdict,
                system_instruction=LICENSING_AGENT_INSTRUCTION + "\n\nYOU ARE NOW IN REFORMATTING MODE. Convert the raw research text verbatim into the SongVerdict schema. Invent no facts. All rules above, especially rule 1 (never suggest, recommend or substitute songs), still apply to every field you emit."
            )
        except Exception as repair_err:
            print(f"Repair pass notice for '{title}': {repair_err}")
            return _unverified_verdict(title, artist_or_source)

    # Hard-filter verdict sources against actual Parallel URLs before saving:
    # Drop any source whose URL isn't in Parallel's returned set.
    seen_urls = PARALLEL_URLS.get() or set()
    normalized_seen = {u.rstrip("/") for u in seen_urls if u}
    if verdict.sources:
        verdict.sources = [
            s for s in verdict.sources
            if s.url and s.url.rstrip("/") in normalized_seen
        ]
    if not verdict.sources and seen_urls:
        verdict.sources = [
            Source(url=u, title="Parallel Web Verification", note="Verified citation from Parallel Search")
            for u in sorted(list(seen_urls))[:4]
        ]

    return verdict



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
