from sqlmodel import Session, select

from backend.database.models import User, UserProfile


def get_user_by_email(session: Session, email: str):
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user(session: Session, user_id: int):
    return session.get(User, user_id)


def create_user(
    session: Session,
    email: str,
    password_hash: str,
):
    user = User(
        email=email,
        password_hash=password_hash,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def create_or_update_profile(
    session: Session,
    user_id: int,
    name: str = "",
    education: str = "",
    location: str = "",
    interests: str = "",
):
    statement = select(UserProfile).where(
        UserProfile.user_id == user_id
    )

    profile = session.exec(statement).first()

    if profile is None:
        profile = UserProfile(
            user_id=user_id,
            name=name,
            education=education,
            location=location,
            interests=interests,
        )
        session.add(profile)
    else:
        profile.name = name
        profile.education = education
        profile.location = location
        profile.interests = interests

    session.commit()
    session.refresh(profile)

    return profile


def get_user_profile(session: Session, user_id: int):
    statement = select(UserProfile).where(
        UserProfile.user_id == user_id
    )

    return session.exec(statement).first() 