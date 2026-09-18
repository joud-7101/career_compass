from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from sqlmodel import Session

# PDF processing
from io import BytesIO
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import pymupdf

from backend.tools.resume_extractor import extract_profile_from_resume
from backend.database.resume_profile import save_resume_file

from backend.routers.auth import router as auth_router

from backend.database.database import (
    create_db_and_tables,
    get_session,
)

from backend.database.crud import (
    get_user,
    get_user_profile,
)


#from backend.graph.graph import career_graph
from backend.schemas.career import CareerRequest

app = FastAPI(
    title="Career Compass API",
    version="0.1.0",
)

app.include_router(auth_router)


@app.on_event("startup")
def startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {
        "message": "Career Compass API is running"
    }
# upload -cv
@app.post("/api/users/me/resume")
async def upload_resume(
    file: UploadFile = File(...)
):
    # Check if the uploaded file is a PDF
    if (
        file.content_type != "application/pdf"
        or not (file.filename or "").lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed."
        )

    # Read the uploaded file
    file_content = await file.read()

    # Check that the file is not empty
    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty."
        )

    # Check PDF file signature
    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The PDF file is invalid or corrupted."
        )

    # Check file size
    max_file_size = 5 * 1024 * 1024  # 5 MB

    if len(file_content) > max_file_size:
        raise HTTPException(
            status_code=400,
            detail="PDF file size must be 5 MB or less."
        )

    # Check if the PDF is valid and not corrupted
    try:
        pdf_reader = PdfReader(
            BytesIO(file_content)
        )

        if len(pdf_reader.pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF has no pages."
            )

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is corrupted or invalid."
        )

    # Extract text from the PDF using PyMuPDF
    extracted_pages = []

    with pymupdf.open(
        stream=file_content,
        filetype="pdf"
    ) as pdf_document:

        for page in pdf_document:
            page_text = page.get_text(
                "text",
                sort=True
            )

            if page_text:
                extracted_pages.append(
                    page_text.strip()
                )

    resume_text = "\n".join(
        extracted_pages
    ).strip()

    # Check that readable text was found
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in the PDF."
        )

    # Extract structured information from the resume
    profile = extract_profile_from_resume(
        resume_text
    )

    # The extracted profile must be reviewed by the user
    profile = profile.model_copy(
        update={
            "review_status": "draft"
        }
    )
    # Save the uploaded PDF file locally
    file_path = save_resume_file(
        file_content
    )
     
    return {
    "status": "success",
    "filename": file.filename,
    "file_path": file_path,
    "content_type": file.content_type,
    "profile": profile.model_dump()
}

@app.post("/api/career")
def career_assistant(
    request: CareerRequest,
    session: Session = Depends(get_session),
):
# Load the career graph only when this endpoint is called.
# This prevents agent-specific dependencies from blocking other API routes.
    from backend.graph.graph import career_graph

    if not user:
        return {
            "error": "User not found"
        }

    profile = get_user_profile(
        session=session,
        user_id=request.user_id,
    )

    user_profile = {
        "name": profile.name if profile else "",
        "education": profile.education if profile else "",
        "experience": [],
        "skills": [],
        "interests": profile.interests if profile else "",
        "location": profile.location if profile else "",
    }

    initial_state = {
        "user_id": request.user_id,
        "query": request.query,
        "user_profile": user_profile,
    }

    result = career_graph.invoke(initial_state)

    return {
        "response": result.get("final_response", ""),
        "jobs": result.get("jobs", []),
        "certifications": result.get("certifications", []),
        "freelance_projects": result.get("freelance_projects", []),
    }