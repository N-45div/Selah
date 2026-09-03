import uuid
import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from ..models import (
    ServicePlan, Song, SongVerdict, ResolveRequest, PlanCreateRequest
)
from ..store import save_plan, get_plan
from ..agents.setlist_agent import (
    parse_setlist_text, parse_setlist_image, convert_extracted_to_songs
)
from ..agents.licensing_agent import research_song
from ..agents.pack_agent import generate_pack_for_setlist
from ..services.pptx_exporter import generate_pptx_deck
from ..services.gemini_client import GeminiQuotaExhaustedError

router = APIRouter(prefix="/api/plan", tags=["Plan"])


async def _run_licensing_research_background(plan_id: str):
    """
    Background worker that researches all songs in a plan concurrently and updates the store as they complete.
    """
    plan = await get_plan(plan_id)
    if not plan:
        return

    async def _research_one(song: Song):
        song.research_status = "researching"
        # Save researching status immediately so frontend sees it
        current = await get_plan(plan_id)
        if current:
            for idx, s in enumerate(current.songs):
                if s.index == song.index:
                    current.songs[idx].research_status = "researching"
                    break
            await save_plan(current)

        try:
            verdict = await research_song(
                title=song.title,
                artist_or_source=song.artist_or_source,
                licenses_held=plan.licenses_held,
                language=song.language
            )
            song.verdict = verdict
            song.research_status = "done"
        except GeminiQuotaExhaustedError as qe:
            print(f"Gemini quota exhausted researching {song.title}: {qe}")
            song.research_status = "error"
            song.error_message = "Gemini quota exhausted — retry after midnight PT"
        except Exception as e:
            print(f"Error researching {song.title}: {e}")
            song.research_status = "error"
            song.error_message = str(e)

        # Update and save plan progressively so frontend poll catches it
        current_plan = await get_plan(plan_id)
        if current_plan:
            for idx, s in enumerate(current_plan.songs):
                if s.index == song.index:
                    current_plan.songs[idx] = song
                    break
            await save_plan(current_plan)

    # Launch all research tasks concurrently
    await asyncio.gather(*[_research_one(s) for s in plan.songs])


@router.post("")
async def create_plan(
    setlist_text: Optional[str] = Form(None),
    service_name: str = Form("Sunday Morning Service"),
    stream_title: str = Form("Sunday Morning Worship & Sermon"),
    licenses_held: str = Form(""),  # comma-separated
    languages: str = Form("English"),
    image_file: Optional[UploadFile] = File(None)
):
    """
    Creates a new service plan from either typed text or an uploaded setlist image.
    Spawns background licensing research tasks for progressive UI display.
    """
    parsed_licenses = [lic.strip() for lic in licenses_held.split(",") if lic.strip()]
    parsed_languages = [lang.strip() for lang in languages.split(",") if lang.strip()]

    # Extract songs from image or text
    if image_file and image_file.filename:
        image_bytes = await image_file.read()
        mime_type = image_file.content_type or "image/jpeg"
        extracted = await parse_setlist_image(image_bytes, mime_type)
    elif setlist_text and setlist_text.strip():
        extracted = await parse_setlist_text(setlist_text)
    else:
        raise HTTPException(status_code=400, detail="Please provide setlist text or upload an image.")

    songs = convert_extracted_to_songs(extracted)
    plan_id = str(uuid.uuid4())[:8]

    plan = ServicePlan(
        id=plan_id,
        service_name=service_name or extracted.service_name or "Sunday Worship",
        stream_title=stream_title,
        languages=parsed_languages,
        licenses_held=parsed_licenses,
        songs=songs,
        status="draft",
        chapters=[]
    )

    await save_plan(plan)

    # Kick off progressive research in the background
    asyncio.create_task(_run_licensing_research_background(plan_id))

    return {
        "plan_id": plan.id,
        "service_name": plan.service_name,
        "song_count": len(plan.songs),
        "status": plan.status
    }


@router.get("/{plan_id}")
async def get_plan_status(plan_id: str):
    """
    Returns full plan JSON including progressive per-song research status and verdict cards.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found.")

    blocking_indices = [s.index for s in plan.blocking_songs]
    return {
        "plan": plan,
        "blocking_songs_count": len(plan.blocking_songs),
        "blocking_indices": blocking_indices,
        "is_ready_for_broadcast": len(plan.blocking_songs) == 0 and all(s.research_status == "done" for s in plan.songs)
    }


@router.post("/{plan_id}/resolve")
async def resolve_song(plan_id: str, payload: ResolveRequest):
    """
    Records a human resolution choice for a blocking (needs_license/unknown) song.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    matched = False
    for song in plan.songs:
        if song.index == payload.song_index:
            song.resolution = payload.resolution
            matched = True
            break

    if not matched:
        raise HTTPException(status_code=400, detail="Song index not found.")

    await save_plan(plan)
    return {"success": True, "remaining_blocking": len(plan.blocking_songs)}


@router.post("/{plan_id}/retry")
async def retry_song(plan_id: str, song_index: int):
    """
    Retries research for a specific song.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    target_song = next((s for s in plan.songs if s.index == song_index), None)
    if not target_song:
        raise HTTPException(status_code=404, detail="Song not found.")

    target_song.research_status = "pending"
    target_song.error_message = None
    await save_plan(plan)

    async def _retry_one():
        try:
            verdict = await research_song(
                title=target_song.title,
                artist_or_source=target_song.artist_or_source,
                licenses_held=plan.licenses_held,
                language=target_song.language
            )
            target_song.verdict = verdict
            target_song.research_status = "done"
        except GeminiQuotaExhaustedError as qe:
            target_song.research_status = "error"
            target_song.error_message = "Gemini quota exhausted — retry after midnight PT"
        except Exception as e:
            target_song.research_status = "error"
            target_song.error_message = str(e)

        current_plan = await get_plan(plan_id)
        if current_plan:
            for idx, s in enumerate(current_plan.songs):
                if s.index == target_song.index:
                    current_plan.songs[idx] = target_song
                    break
            await save_plan(current_plan)

    asyncio.create_task(_retry_one())
    return {"success": True, "message": "Retry started."}


@router.post("/{plan_id}/slides")
async def build_slides(plan_id: str):
    """
    Builds slides for all songs adhering to copyright lyrics policy and Indic transliteration.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    updated_songs = await generate_pack_for_setlist(plan.songs)
    plan.songs = updated_songs
    await save_plan(plan)

    total_slides = sum(len(s.slides) for s in plan.songs)
    return {
        "success": True,
        "total_slides": total_slides,
        "songs": [s.model_dump() for s in plan.songs]
    }


# ---------- Server-Sent Events (SSE) Live Research Telemetry ----------

@router.get("/{plan_id}/stream")
async def stream_plan_telemetry(plan_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time research telemetry.
    Replaces frontend 1.5s HTTP polling with a persistent event stream that pushes
    progressive song verdicts, research status changes, and plan readiness events.
    """
    async def event_generator():
        max_ticks = 300  # Safety cap: ~5 minutes max stream
        for _ in range(max_ticks):
            plan = await get_plan(plan_id)
            if not plan:
                yield f"event: error\ndata: {json.dumps({'error': 'Plan not found'})}\n\n"
                break

            # Build per-song status payload
            songs_payload = []
            for s in plan.songs:
                song_data = {
                    "index": s.index,
                    "title": s.title,
                    "artist_or_source": s.artist_or_source,
                    "research_status": s.research_status,
                    "error_message": s.error_message,
                    "resolution": s.resolution
                }
                if s.verdict:
                    song_data["verdict"] = {
                        "legal_status": s.verdict.legal_status.value,
                        "legal_summary": s.verdict.legal_summary,
                        "content_id_risk": s.verdict.content_id_risk.value,
                        "content_id_summary": s.verdict.content_id_summary,
                        "owner": s.verdict.owner,
                        "ccli_number": s.verdict.ccli_number,
                        "sources": [src.model_dump() for src in s.verdict.sources]
                    }
                songs_payload.append(song_data)

            blocking_indices = [s.index for s in plan.blocking_songs]
            all_done = all(s.research_status in ("done", "error") for s in plan.songs)
            is_ready = len(plan.blocking_songs) == 0 and all_done

            data_payload = {
                "id": plan.id,
                "status": plan.status,
                "songs": songs_payload,
                "blocking_count": len(plan.blocking_songs),
                "blocking_indices": blocking_indices,
                "is_ready_for_broadcast": is_ready
            }

            yield f"event: plan_update\ndata: {json.dumps(data_payload)}\n\n"

            # Stream completion: all songs researched and plan is not live
            if all_done and plan.status != "live":
                yield f"event: research_complete\ndata: {json.dumps({'plan_id': plan.id, 'is_ready': is_ready})}\n\n"
                break

            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ---------- PowerPoint 16:9 Slide Deck Export ----------

@router.get("/{plan_id}/export/pptx")
async def export_pptx(plan_id: str):
    """
    Generates and downloads a 16:9 widescreen PowerPoint slide deck
    with dark broadcast styling, verse/chorus splits, and transliteration.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    pptx_buffer = generate_pptx_deck(plan)
    filename = f"selah_slides_{plan_id}.pptx"

    return Response(
        content=pptx_buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

