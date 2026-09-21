from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session

from backend.database.database import get_session
from backend.database.models import PortfolioLink
from backend.tools.portfolio_extractor import extract_portfolio_profile


router = APIRouter(
    prefix="/api/users/me/portfolio",
    tags=["portfolio"],
)


class PortfolioRequest(BaseModel):
    url: HttpUrl


@router.post("")
def add_portfolio(
    request: PortfolioRequest,
    session: Session = Depends(get_session),
):
    portfolio = PortfolioLink(
        user_id=1,  # temporary until authentication is connected
        url=str(request.url),
        source="website",
        status="pending",
    )

    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)

    try:
        extraction = extract_portfolio_profile(
            str(request.url)
        )

        portfolio.status = "completed"
        portfolio.error_message = ""

        session.commit()

        return {
            "message": "Portfolio extracted successfully.",
            "id": portfolio.id,
            "url": portfolio.url,
            "status": portfolio.status,
            "profile": extraction.model_dump(),
        }

    except Exception as exc:
        portfolio.status = "failed"
        portfolio.error_message = str(exc)

        session.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Portfolio extraction failed: {exc}",
        )
