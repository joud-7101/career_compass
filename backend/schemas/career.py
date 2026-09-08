from pydantic import BaseModel, Field


class CareerRequest(BaseModel):

    user_id: str

    query: str = Field(
        min_length=1,
        description="The user's career request"
    )


class UserProfileRequest(BaseModel):

    user_id: str
    name: str
    education: str = ""
    location: str = ""

    skills: list[str] = []
    experience: list[str] = []
    interests: list[str] = []