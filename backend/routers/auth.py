import json

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session
from typing import Optional

from backend.database.database import get_session
from backend.database.crud import (
    get_user_by_email,
    create_user,
    get_profile_review,
    create_or_update_profile_review,
)
from backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# --------------------------------------------------
# Helper: resolve the authenticated user_id from
# an "Authorization: Bearer <token>" header.
# --------------------------------------------------

def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# --------------------------------------------------
# POST /api/auth/register
# --------------------------------------------------

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    session: Session = Depends(get_session),
):
    existing_user = get_user_by_email(session, request.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = create_user(
        session=session,
        email=request.email,
        password_hash=hash_password(request.password),
    )

    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


# --------------------------------------------------
# POST /api/auth/login
# --------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    session: Session = Depends(get_session),
):
    user = get_user_by_email(session, request.email)

    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


# --------------------------------------------------
# GET /api/auth/me
# Returns the current user's info + stored profile
# --------------------------------------------------

@router.get("/me")
def get_me(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    from backend.database.crud import get_user
    user = get_user(session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_review = get_profile_review(session, user_id)

    profile_data = None
    if profile_review and profile_review.profile_data:
        try:
            profile_data = json.loads(profile_review.profile_data)
        except json.JSONDecodeError:
            profile_data = None

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "profile": profile_data,
    }


# --------------------------------------------------
# POST /api/auth/profile
# Saves the reviewed UserProfile JSON for the
# authenticated user.
# --------------------------------------------------

@router.post("/profile", status_code=status.HTTP_200_OK)
def save_profile(
    profile_payload: dict,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    profile_json = json.dumps(profile_payload)

    create_or_update_profile_review(
        session=session,
        user_id=user_id,
        profile_data=profile_json,
        review_status="approved",
    )

    return {"message": "Profile saved successfully."}