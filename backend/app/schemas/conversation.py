from datetime import datetime
from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.conversation import ConversationMode, ConversationStatus
from app.schemas.common import ensure_utc

MAX_SPEAKERS = 10


def is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class SpeakerIn(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    designation: str | None = Field(default=None, max_length=150)
    bio: str | None = Field(default=None, max_length=5000)
    photo_url: str | None = Field(default=None, max_length=500)


class SpeakerOut(SpeakerIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_order: int


class ConversationCreate(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "title": "Founders & Funding: Early-Stage Lessons",
                    "description": "An open conversation on raising a first round.",
                    "scheduled_at": "2026-12-20T14:30:00Z",
                    "duration_minutes": 90,
                    "mode": "online",
                    "location_or_link": "https://meet.example.com/abc",
                    "capacity": 100,
                    "cover_image_url": None,
                    "speakers": [
                        {
                            "name": "Rohan Mehta",
                            "designation": "Partner, XYZ Ventures",
                            "bio": "Investor in 30+ early-stage startups.",
                            "photo_url": None,
                        }
                    ],
                }
            ]
        },
    )

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10000)
    scheduled_at: datetime
    duration_minutes: int = Field(ge=15, le=480)
    mode: ConversationMode
    location_or_link: str = Field(min_length=1, max_length=500)
    capacity: int | None = Field(default=None, ge=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    speakers: list[SpeakerIn] = Field(default_factory=list, max_length=MAX_SPEAKERS)

    @field_validator("scheduled_at")
    @classmethod
    def normalize_scheduled_at(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("location_or_link")
    @classmethod
    def validate_location_or_link(cls, value: str, info) -> str:
        value = value.strip()
        if (
            info.data.get("mode") == ConversationMode.ONLINE
            and not is_valid_http_url(value)
        ):
            raise ValueError(
                "location_or_link must be a valid http(s) URL when mode is 'online'"
            )
        return value


class ConversationUpdate(BaseModel):
    """Partial update. Omitting a field leaves it unchanged.

    An omitted `speakers` list leaves speakers untouched; a provided list
    (even an empty one) replaces the whole list.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=10000)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    mode: ConversationMode | None = None
    location_or_link: str | None = Field(default=None, min_length=1, max_length=500)
    capacity: int | None = Field(default=None, ge=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    speakers: list[SpeakerIn] | None = Field(default=None, max_length=MAX_SPEAKERS)

    @field_validator("scheduled_at")
    @classmethod
    def normalize_scheduled_at(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    scheduled_at: datetime
    duration_minutes: int
    mode: ConversationMode
    location_or_link: str
    capacity: int | None
    cover_image_url: str | None
    status: ConversationStatus
    speakers: list[SpeakerOut] = Field(default_factory=list)


__all__ = [
    "ConversationCreate",
    "ConversationOut",
    "ConversationUpdate",
    "SpeakerIn",
    "SpeakerOut",
    "is_valid_http_url",
]
