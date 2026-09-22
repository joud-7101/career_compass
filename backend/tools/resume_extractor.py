"""import os

from dotenv import load_dotenv
from openai import OpenAI

from backend.schemas.profile import UserProfile


load_dotenv()


def extract_profile_from_resume(
    resume_text: str
) -> UserProfile:

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.responses.create(
        model="gpt-4o-mini",

        instructions=(
           # "You extract structured information from resumes. "
            #"Use only information explicitly found in the resume. "
            #"Do not invent missing information. "
            #"Return the information using the provided schema."
             "You extract structured information from resumes. "
                        "Use only information explicitly written in the resume. "
                        "Do not infer, guess, or invent missing information. "
            
                        "For top-level skills, extract every skill explicitly listed "
                        "in the resume's Skills or Key Skills section. "
                        "Preserve the wording used in the resume and do not merge "
                        "different skill names. "
            
                        "For experience.skills, only include skills that are explicitly "
                        "associated with that specific experience in the resume. "
                        "Do not infer skills from job responsibilities. "
                        "If none are explicitly provided, return an empty list. "
            
                        "If information is missing, use null or an empty list "
                        "according to the schema. "
            
                        "The review_status must always be draft."
        ),

        input=resume_text,

        text={
            "format": {
                "type": "json_schema",
                "name": "user_profile",
                "schema": UserProfile.model_json_schema(),
                "strict": False,
            }
        },
    )

    profile = UserProfile.model_validate_json(
        response.output_text
    )

    return profile
    
    """ 
"""import os

from dotenv import load_dotenv
from openai import OpenAI

from backend.schemas.profile import UserProfile


load_dotenv()


def extract_profile_from_resume(
    resume_text: str
) -> UserProfile:

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.responses.parse(
        model="gpt-4o-mini",

        instructions=(
            "You extract structured information from resumes. "
            "Use only information explicitly written in the resume. "
            "Do not infer, guess, or invent missing information. "

            "For top-level skills, extract every skill explicitly listed "
            "in the resume's Skills or Key Skills section. "
            "Preserve the wording used in the resume and do not merge "
            "different skill names. "

            "For experience.skills, only include skills that are explicitly "
            "associated with that specific experience in the resume. "
            "Do not infer skills from job responsibilities. "
            "If none are explicitly provided, return an empty list. "

            "If information is missing, use null or an empty list "
            "according to the schema. "

            "The review_status must always be draft."
        ),

        input=resume_text,

        text_format=UserProfile,
    )

    profile = response.output_parsed

    if profile is None:
        raise ValueError(
            "The resume could not be converted into a structured profile."
        )

    return profile
"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from backend.schemas.profile import UserProfile


load_dotenv()


def extract_profile_from_resume(
    resume_text: str
) -> UserProfile:

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.responses.create(
        model= "gpt-4.1-mini",#"gpt-4o-mini",

        instructions=(
             "You extract structured information from resumes. "
             "Use only information explicitly written in the resume. "
             "Do not infer, guess, or invent missing information. "

              "For each work experience, include all explicitly written "
             "job responsibilities in the description field. "
              "Do not omit the description when responsibilities are present. "

             "For top-level skills, return each skill as an object "
             "with name, level, and source fields. "
             "Preserve every explicitly listed skill. "

             "For experience.skills, only include skills explicitly "
             "associated with that experience. "
             "Do not infer skills from responsibilities. "

              "If information is missing, use null or an empty list. "
             "The review_status must always be draft. "
              "Return the information using the provided schema."
              "All information extracted from this document comes from a resume. "
              "When a source field is used, set source.kind to 'resume'. "
             
        ),

        input=resume_text,

        text={
            "format": {
                "type": "json_schema",
                "name": "user_profile",
                "schema": UserProfile.model_json_schema(),
                "strict": False,
            }
        },
    )

    data = json.loads(
        response.output_text
    )

    # Normalize skills if the model returns strings
    normalized_skills = []

    for skill in data.get("skills", []):
        if isinstance(skill, str):
            normalized_skills.append({
                "name": skill,
                "level": None,
                "source": None,
            })
        else:
            normalized_skills.append(skill)

    data["skills"] = normalized_skills
    data["review_status"] = "draft"

    # Normalize professional links
    for link in data.get("professional_links", []):
        if isinstance(link, dict):
            url = link.get("url")

            if url and not url.startswith(("http://", "https://")):
                link["url"] = "https://" + url

    profile = UserProfile.model_validate(
        data
    )

    return profile
