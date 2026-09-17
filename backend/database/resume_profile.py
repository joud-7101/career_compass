from pathlib import Path
from uuid import uuid4

from sqlmodel import Session

from backend.schemas.profile import UserProfile


RESUME_DIR = Path("data/resumes")


def save_resume_file(
    file_content: bytes
) -> str:
    """
    Save the uploaded resume PDF locally
    and return its file path.
    """

    RESUME_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_name = f"{uuid4().hex}.pdf"
    file_path = RESUME_DIR / file_name

    file_path.write_bytes(
        file_content
    )

    return str(file_path)


def save_extracted_profile(
    session: Session,
    user_id: int,
    profile: UserProfile,
    file_path: str,
    original_filename: str,
):
    """
    Save extracted CV data to the database.

    This function will be completed after the final
    database schema is aligned with UserProfile.
    """

    return {
        "user_id": user_id,
        "file_path": file_path,
        "original_filename": original_filename,
        "profile": profile.model_dump(),
    }