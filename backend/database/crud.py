from sqlmodel import Session

from backend.database.models import User


def create_user(
    session: Session,
    user_id: str,
    name: str,
    education: str = "",
    location: str = "",
    skills: str = "",
    experience: str = "",
    interests: str = "",
):

    user = User(
        id=user_id,
        name=name,
        education=education,
        location=location,
        skills=skills,
        experience=experience,
        interests=interests,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def get_user(session: Session, user_id: str):

    return session.get(User, user_id)