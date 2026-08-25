import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..store import get_plan

router = APIRouter(prefix="/api/plan", tags=["Stream"])


@router.get("/{plan_id}/stream")
async def stream_plan_telemetry(plan_id: str):
    """
    Server-Sent Events (SSE) endpoint streaming real-time licensing research progress,
    verdict arrivals, and live broadcast telemetry to connected clients.
    """
    plan = await get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Service plan not found.")

    async def event_generator():
        last_state = ""
        while True:
            current_plan = await get_plan(plan_id)
            if not current_plan:
                break

            payload = {
                "id": current_plan.id,
                "status": current_plan.status,
                "started_at": current_plan.started_at,
                "current_slide_index": current_plan.current_slide_index,
                "blocking_songs_count": len(current_plan.blocking_songs),
                "songs": [
                    {
                        "index": s.index,
                        "title": s.title,
                        "artist": s.artist_or_source,
                        "status": s.research_status,
                        "resolution": s.resolution,
                        "verdict": s.verdict.model_dump() if s.verdict else None
                    }
                    for s in current_plan.songs
                ]
            }

            serialized = json.dumps(payload, ensure_ascii=False)
            if serialized != last_state:
                last_state = serialized
                yield f"event: plan_update\ndata: {serialized}\n\n"

            # If all research is done and stream is not live, we can close the SSE stream after delivering final state
            all_done = all(s.research_status in ("done", "error") for s in current_plan.songs)
            if all_done and current_plan.status in ("ready", "ended"):
                # Send one final complete message and exit loop
                yield f"event: research_complete\ndata: {serialized}\n\n"
                break

            await asyncio.sleep(0.8)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
