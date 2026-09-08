from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):

    id: str = Field(primary_key=True)

    name: str

    education: str | None = None

    location: str | None = None

    skills: str = ""

    experience: str = ""

    interests: str = ""