import re
from enum import Enum
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator


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
    url: str = Field(default="", description="Primary source URL")
    title: str = Field(default="Citation", description="Source title")
    note: str = Field(default="", description="One line: what this source establishes")

    @field_validator("url", mode="before")
    @classmethod
    def coerce_url(cls, v: Any) -> str:
        return str(v).strip() if v else ""

    @field_validator("title", mode="before")
    @classmethod
    def coerce_title(cls, v: Any) -> str:
        return str(v).strip() if v else "Citation"

    @field_validator("note", mode="before")
    @classmethod
    def coerce_note(cls, v: Any) -> str:
        return str(v).strip() if v else ""


class SongVerdict(BaseModel):
    legal_status: LegalStatus
    legal_summary: str = Field(
        default="Broadcast rights and licensing assessment completed.",
        description="2-3 plain sentences a volunteer understands"
    )
    content_id_risk: ContentIdRisk
    content_id_summary: str = Field(
        default="No specific YouTube Content ID claims detected; standard livestream broadcast guidelines apply.",
        description="Clear explanation of YouTube Content ID risk and mitigation"
    )
    owner: str = Field(default="", description="Copyright owner or administrator")
    publication_year: Optional[int] = Field(default=None, description="Original publication year if known / verified (critical for public domain assertions)")
    ccli_number: Optional[Union[str, int]] = Field(default=None, description="CCLI song select number if found")
    options: List[str] = Field(
        default_factory=list,
        description="Actions for humans (e.g. mute during stream, acquire license, verify arrangement) — NEVER alternative songs"
    )
    sources: List[Source] = Field(default_factory=list)
    attribution_line: str = Field(
        default="",
        description="Ready-to-paste attribution for video description (e.g., Song - Artist © Year Publisher CCLI #...)"
    )

    @field_validator("ccli_number", mode="before")
    @classmethod
    def coerce_ccli_number(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        s = str(v).strip()
        if not s or s.lower() in ("null", "none", "n/a", "unknown"):
            return None
        return s

    @field_validator("content_id_summary", mode="before")
    @classmethod
    def coerce_content_id_summary(cls, v: Any) -> str:
        if v is None:
            return "No specific YouTube Content ID claims detected; standard livestream broadcast guidelines apply."
        s = str(v).strip()
        if not s or s.lower() in ("null", "none"):
            return "No specific YouTube Content ID claims detected; standard livestream broadcast guidelines apply."
        return s

    @field_validator("legal_summary", mode="before")
    @classmethod
    def coerce_legal_summary(cls, v: Any) -> str:
        if v is None or not str(v).strip():
            return "Broadcast rights and licensing assessment completed."
        return str(v).strip()

    @field_validator("owner", mode="before")
    @classmethod
    def coerce_owner(cls, v: Any) -> str:
        return str(v).strip() if v is not None else ""

    @field_validator("attribution_line", mode="before")
    @classmethod
    def coerce_attribution_line(cls, v: Any) -> str:
        return str(v).strip() if v is not None else ""

    @field_validator("publication_year", mode="before")
    @classmethod
    def coerce_publication_year(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s or s.lower() in ("null", "none", "unknown", "n/a"):
                return None
            m = re.search(r"\b(1\d{3}|20\d{2})\b", s)
            if m:
                return int(m.group(1))
        return None

    @field_validator("legal_status", mode="before")
    @classmethod
    def coerce_legal_status(cls, v: Any) -> LegalStatus:
        if isinstance(v, LegalStatus):
            return v
        if isinstance(v, str):
            clean = v.strip().lower().replace(" ", "_").replace("-", "_")
            for member in LegalStatus:
                if member.value == clean:
                    return member
        return LegalStatus.UNKNOWN

    @field_validator("content_id_risk", mode="before")
    @classmethod
    def coerce_content_id_risk(cls, v: Any) -> ContentIdRisk:
        if isinstance(v, ContentIdRisk):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            for member in ContentIdRisk:
                if member.value == clean:
                    return member
        return ContentIdRisk.HIGH

    @field_validator("options", mode="before")
    @classmethod
    def coerce_options(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(item).strip() for item in v if item and str(item).strip()]
        return []

    @field_validator("sources", mode="before")
    @classmethod
    def coerce_sources(cls, v: Any) -> List[Any]:
        if v is None:
            return []
        if isinstance(v, list):
            valid = []
            for item in v:
                if isinstance(item, (dict, Source)):
                    valid.append(item)
                elif isinstance(item, str) and item.strip():
                    valid.append({"url": item.strip(), "title": item.strip(), "note": ""})
            return valid
        return []


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
        """Songs that block going live: unresolved needs_license/unknown, errors, or still researching."""
        blocking = []
        for s in self.songs:
            if s.verdict and s.verdict.legal_status in (LegalStatus.NEEDS_LICENSE, LegalStatus.UNKNOWN):
                if not s.resolution:
                    blocking.append(s)
            elif s.research_status == "error" and not s.resolution:
                blocking.append(s)
            elif s.research_status in ("pending", "researching") and not s.resolution:
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
    song_index: int = Field(ge=0)
    resolution: str = Field(min_length=1, max_length=300)



class AdvanceRequest(BaseModel):
    slide_index: int


class ChapterRequest(BaseModel):
    label: str
