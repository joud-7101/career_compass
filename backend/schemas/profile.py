"""Versioned contracts for CV and portfolio profile ingestion.

These models are the API boundary between extractors, the database layer, the
profile-review UI, and the career graph.  A user-approved profile is the only
profile that should be supplied to specialist agents.
"""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


SCHEMA_VERSION = "1.0"


class ProfileSource(BaseModel):
    """Where an extracted field originated and how reliable it is."""

    kind: Literal["user", "resume", "github", "portfolio", "manual"]
    reference: str | None = Field(
        default=None,
        description="Document ID, repository URL, or other traceable source.",
    )
    confidence: float | None = Field(default=None, ge=0, le=1)


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    source: ProfileSource | None = None


class Experience(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    skills: list[str] = Field(default_factory=list)
    source: ProfileSource | None = None


class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: HttpUrl | None = None
    repository_url: HttpUrl | None = None
    source: ProfileSource | None = None


class Skill(BaseModel):
    name: str
    level: Literal["beginner", "intermediate", "advanced"] | None = None
    source: ProfileSource | None = None


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    credential_id: str | None = None
    credential_url: HttpUrl | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    source: ProfileSource | None = None


class PortfolioLink(BaseModel):
    url: HttpUrl
    kind: Literal["github", "personal_website", "behance", "other"]
    label: str | None = None


class UserProfile(BaseModel):
    """The normalized, reviewed profile that powers all career agents."""

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    name: str = ""
    headline: str | None = None
    location: str | None = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    portfolio_links: list[PortfolioLink] = Field(default_factory=list)
    review_status: Literal["draft", "approved"] = "draft"


class ProfileExtractionDraft(BaseModel):
    """Extractor output; it must be reviewed before it replaces a profile."""

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    profile: UserProfile
    extraction_warnings: list[str] = Field(default_factory=list)

