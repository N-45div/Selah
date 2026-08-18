from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LegalStatus(str, Enum):
    PUBLIC_DOMAIN = "public_domain"
    COVERED = "covered"
    NEEDS_LICENSE = "needs_license"
    UNKNOWN = "unknown"


class ContentIdRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Source(BaseModel):
    url: str
    title: str
    note: str = Field(description="One line: what this source establishes")


class SongVerdict(BaseModel):
    legal_status: LegalStatus
    legal_summary: str = Field(description="2-3 plain sentences a volunteer understands")
    content_id_risk: ContentIdRisk
    content_id_summary: str = Field(description="Clear explanation of YouTube Content ID risk and mitigation")
    owner: str = Field(default="", description="Copyright owner or administrator")
    ccli_number: Optional[str] = Field(default=None, description="CCLI song select number if found")
    options: List[str] = Field(
        default_factory=list,
        description="Actions for humans (e.g. mute during stream, acquire license, verify arrangement) — NEVER alternative songs"
    )
    sources: List[Source] = Field(default_factory=list)
    attribution_line: str = Field(
        default="",
        description="Ready-to-paste attribution for video description (e.g., Song - Artist © Year Publisher CCLI #...)"
    )


class Slide(BaseModel):
    song_index: int
    label: str = Field(description="Section label like Verse 1, Chorus, Bridge")
    lines: List[str] = Field(default_factory=list)
    transliteration: List[str] = Field(default_factory=list)


class Song(BaseModel):
    index: int
    title: str
    artist_or_source: str = ""
    language: str = "English"
    research_status: str = "pending"  # "pending", "done", "error"
    error_message: Optional[str] = None
    verdict: Optional[SongVerdict] = None
    resolution: Optional[str] = None
    slides: List[Slide] = Field(default_factory=list)
    lyrics_policy: str = "full"  # "full" for public domain, "first_line_only" / placeholder for copyrighted


class ChapterMark(BaseModel):
    seconds_from_start: int
    label: str
    timestamp_str: str  # e.g., "0:00", "14:25"


class ServicePlan(BaseModel):
    id: str
    service_name: str
    stream_title: str
    languages: List[str] = Field(default_factory=lambda: ["English"])
    licenses_held: List[str] = Field(default_factory=list)
    songs: List[Song] = Field(default_factory=list)
    status: str = "draft"  # "draft", "ready", "live", "ended"
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    current_slide_index: int = 0
    chapters: List[ChapterMark] = Field(default_factory=list)

    @property
    def blocking_songs(self) -> List[Song]:
        """Songs whose verdict is needs_license or unknown and haven't been resolved yet."""
        blocking = []
        for s in self.songs:
            if s.verdict and s.verdict.legal_status in (LegalStatus.NEEDS_LICENSE, LegalStatus.UNKNOWN):
                if not s.resolution:
                    blocking.append(s)
            elif s.research_status == "error" and not s.resolution:
                blocking.append(s)
        return blocking


class CloseoutPack(BaseModel):
    plan_id: str
    youtube_description: str
    ccli_usage_log: str
    chapters_text: str
    dispute_pack: str


# Request Models
class PlanCreateRequest(BaseModel):
    setlist_text: Optional[str] = None
    service_name: str = "Sunday Morning Service"
    stream_title: str = "Sunday Morning Worship & Sermon"
    languages: List[str] = Field(default_factory=lambda: ["English"])
    licenses_held: List[str] = Field(default_factory=list)


class ResolveRequest(BaseModel):
    song_index: int
    resolution: str


class AdvanceRequest(BaseModel):
    slide_index: int


class ChapterRequest(BaseModel):
    label: str
