from io import BytesIO

import pymupdf
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlmodel import Session

from backend.database.database import get_session
from backend.database.models import ResumeDocument
from backend.database.resume_profile import (
    save_extracted_profile,
    save_resume_file,
)
from backend.routers.auth import get_current_user_id
from backend.tools.resume_extractor import (
    extract_profile_from_resume,
)
from backend.tools.portfolio_extractor import (
    extract_portfolio_profile,
)
from backend.database.profile_merge import (
    merge_profiles,
)


# --------------------------------------------------
# Resume Router
# --------------------------------------------------

router = APIRouter(
    prefix="/api/users/me",
    tags=["Resume"],
)


# --------------------------------------------------
# POST /api/users/me/resume
# Upload and process the authenticated user's CV
# --------------------------------------------------

@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):

    # --------------------------------------------------
    # 1. Validate file type
    # Only PDF files are allowed
    # --------------------------------------------------

    if (
        file.content_type != "application/pdf"
        or not (file.filename or "").lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed.",
        )


    # --------------------------------------------------
    # 2. Read uploaded file
    # --------------------------------------------------

    file_content = await file.read()


    # --------------------------------------------------
    # 3. Check that the uploaded file is not empty
    # --------------------------------------------------

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )


    # --------------------------------------------------
    # 4. Check PDF file signature
    # A valid PDF normally starts with %PDF-
    # --------------------------------------------------

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The PDF file is invalid or corrupted.",
        )


    # --------------------------------------------------
    # 5. Check file size
    # Maximum allowed size = 5 MB
    # --------------------------------------------------

    max_file_size = 5 * 1024 * 1024

    if len(file_content) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail="PDF file size must be 5 MB or less.",
        )


    # --------------------------------------------------
    # 6. Validate the PDF using pypdf
    # Check that it is readable and contains pages
    # --------------------------------------------------

    try:
        pdf_reader = PdfReader(
            BytesIO(file_content)
        )

        if len(pdf_reader.pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF has no pages.",
            )

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is corrupted or invalid.",
        )


    # --------------------------------------------------
    # 7. Extract text from PDF using PyMuPDF
    # sort=True helps preserve text order
    # --------------------------------------------------

    extracted_pages = []

    with pymupdf.open(
        stream=file_content,
        filetype="pdf",
    ) as pdf_document:

        for page in pdf_document:

            page_text = page.get_text(
                "text",
                sort=True,
            )

            if page_text:
                extracted_pages.append(
                    page_text.strip()
                )


    # Combine text from all PDF pages
    resume_text = "\n".join(
        extracted_pages
    ).strip()


    # --------------------------------------------------
    # 8. Make sure readable text was extracted
    # --------------------------------------------------

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in the PDF.",
        )


    # --------------------------------------------------
    # 9. Send resume text to the LLM
    # Convert the CV into a structured UserProfile
    # --------------------------------------------------

    profile = extract_profile_from_resume(
        resume_text
    )


    # The extracted profile must be reviewed
    # before becoming the final approved profile
    profile = profile.model_copy(
        update={
            "review_status": "draft"
        }
    )


    # --------------------------------------------------
    # 10. Save the uploaded PDF locally
    # --------------------------------------------------

    file_path = save_resume_file(
        file_content
    )


    # --------------------------------------------------
    # 11. Save resume file information in resume_documents
    # --------------------------------------------------

    resume_document = ResumeDocument(
        user_id=user_id,
        file_path=file_path,
        original_filename=(
            file.filename or "resume.pdf"
        ),
        status="processed",
        error_message="",
    )

    # ---------------------------------
    # Save ResumeDocument
    # ---------------------------------

    # Add the uploaded CV information to the database session.
    # The final commit will happen when the extracted profile is saved.
    session.add(resume_document)


    # ---------------------------------
    # Save extracted profile
    # ---------------------------------

    # Save the structured CV data into the related database tables.
    save_extracted_profile(
        session=session,
        user_id=user_id,
        profile=profile,
    )


    # ---------------------------------
    # Return result to frontend
    # ---------------------------------

    # Send the extracted profile back to upload_cv.py
    # so it can be displayed on the Profile Review page.
    return {
        "status": "success",
        "filename": file.filename,
        "file_path": file_path,
        "content_type": file.content_type,
        "profile": profile.model_dump(
            mode="json"
        ),
    }
# --------------------------------------------------
# POST /api/users/me/profile/extract
# Extract and merge CV + Portfolio
# --------------------------------------------------

@router.post("/profile/extract")
async def extract_combined_profile(
    file: UploadFile = File(...),
    portfolio_url: str | None = Form(None),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # --------------------------------------------------
    # 1. Validate CV
    # --------------------------------------------------

    if (
        file.content_type != "application/pdf"
        or not (file.filename or "").lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The PDF file is invalid or corrupted.",
        )

    max_file_size = 5 * 1024 * 1024

    if len(file_content) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail="PDF file size must be 5 MB or less.",
        )

    # --------------------------------------------------
    # 2. Validate and extract CV text
    # --------------------------------------------------

    try:
        pdf_reader = PdfReader(
            BytesIO(file_content)
        )

        if len(pdf_reader.pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF has no pages.",
            )

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is corrupted or invalid.",
        )

    extracted_pages = []

    with pymupdf.open(
        stream=file_content,
        filetype="pdf",
    ) as pdf_document:

        for page in pdf_document:
            page_text = page.get_text(
                "text",
                sort=True,
            )

            if page_text:
                extracted_pages.append(
                    page_text.strip()
                )

    resume_text = "\n".join(
        extracted_pages
    ).strip()

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in the PDF.",
        )

    # --------------------------------------------------
    # 3. Extract CV profile
    # --------------------------------------------------

    try:
        cv_profile = extract_profile_from_resume(
            resume_text
        )

        cv_profile = cv_profile.model_copy(
            update={
                "review_status": "draft"
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"CV extraction failed: {exc}",
        )

    # --------------------------------------------------
    # 4. Extract portfolio profile if provided
    # --------------------------------------------------

    portfolio_profile = None
    portfolio_warnings = []

    if portfolio_url:
        try:
            portfolio_extraction = extract_portfolio_profile(
                portfolio_url
            )

            portfolio_profile = (
                portfolio_extraction.profile
            )

            portfolio_warnings = (
                portfolio_extraction.extraction_warnings
            )

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Portfolio extraction failed: {exc}",
            )

    # --------------------------------------------------
    # 5. Merge CV + Portfolio
    # --------------------------------------------------

    merged_profile = merge_profiles(
        cv_profile=cv_profile,
        portfolio_profile=portfolio_profile,
        portfolio_url=portfolio_url,
    )
    print("MERGED PROJECTS:")
    for project in merged_profile.projects:
        print("-", project.name, "->", project.source.kind if project.source else None)

    print("MERGED SKILLS:")
    for skill in merged_profile.skills:
        print("-", skill.name, "->", skill.source.kind if skill.source else None)

    # --------------------------------------------------
    # 6. Save CV file
    # --------------------------------------------------

    file_path = save_resume_file(
        file_content
    )

    resume_document = ResumeDocument(
        user_id=user_id,
        file_path=file_path,
        original_filename=(
            file.filename or "resume.pdf"
        ),
        status="processed",
        error_message="",
    )

    session.add(resume_document)

    # --------------------------------------------------
    # 7. Save merged profile
    # --------------------------------------------------

    save_extracted_profile(
        session=session,
        user_id=user_id,
        profile=merged_profile,
    )

    return {
        "status": "success",
        "filename": file.filename,
        "file_path": file_path,
        "profile": merged_profile.model_dump(
            mode="json"
        ),
        "portfolio_included": (
            portfolio_profile is not None
        ),
        "portfolio_warnings": portfolio_warnings,
    }