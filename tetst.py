from backend.graph.state import CareerState

from backend.agents.job_agent import job_agent
from backend.agents.freelance_agent import freelance_agent
from backend.agents.certification_agent import certification_agent

from backend.schemas.profile import UserProfile


def main():

    # ============================================================
    # TEST USER PROFILE
    # ============================================================

    test_profile = UserProfile(
        personal_information={
            "name": "Joud",
            "location": "Saudi Arabia",
        },

        professional_summary=(
            "Fresh Software Engineering graduate interested in "
            "AI, software engineering, and web development."
        ),

        education=[
            {
                "institution": "University of Jeddah",
                "degree": "BSc",
                "field_of_study": "Software Engineering",
                "start_date": "2022",
                "end_date": "2026",
            }
        ],

        experience=[
            {
                "title": "Software Engineering Intern",
                "company": "Sallam Tech",
                "location": "Saudi Arabia",
                "start_date": "2026",
                "end_date": "2026",
                "description": (
                    "Worked on web development using React and "
                    "JavaScript and contributed to frontend development."
                ),
                "skills": [
                    "React",
                    "JavaScript",
                    "HTML",
                    "CSS",
                ],
            }
        ],

        skills=[
            {"name": "Python"},
            {"name": "JavaScript"},
            {"name": "React"},
            {"name": "HTML"},
            {"name": "CSS"},
            {"name": "FastAPI"},
            {"name": "RAG"},
            {"name": "LLMs"},
            {"name": "Git"},
        ],

        certifications=[],

        projects=[],

        languages=[
            "Arabic",
            "English",
        ],

        professional_links=[],

        achievements=[],

        volunteering=[],

        review_status="approved",
    )

    # ============================================================
    # TEST CAREER STATE
    # ============================================================

    test_state: CareerState = {
        "user_profile": test_profile,

        "query": (
            "Find entry-level AI Engineer and Software Engineer "
            "opportunities in Saudi Arabia and recommend relevant "
            "certifications."
        ),

        # These are included because the current certification_agent
        # reads them directly from state instead of user_profile.
        "education": test_profile.education,
        "experience": test_profile.experience,
        "skills": test_profile.skills,
        "interests": [
            "AI",
            "Software Engineering",
            "Web Development",
            "Agentic AI",
        ],
    }

    # ============================================================
    # DISPLAY PROFILE
    # ============================================================

    print("=" * 70)
    print("CAREER COMPASS - AGENT TEST")
    print("=" * 70)

    print("\nPROFILE TYPE:")
    print(type(test_state["user_profile"]))

    print("\nPROFILE:")
    print(test_state["user_profile"])

    # ============================================================
    # 1. TEST JOB AGENT
    # ============================================================

    print("\n\n" + "=" * 70)
    print("1. TESTING JOB AGENT")
    print("=" * 70)

    try:
        job_result = job_agent(test_state)

        jobs = job_result.get("jobs", [])

        if not jobs:
            print("\nNo jobs returned.")

        else:
            print(f"\nFound {len(jobs)} job(s).\n")

            for i, job in enumerate(jobs, start=1):

                print("-" * 70)
                print(f"JOB #{i}")

                print(f"Title: {job.title}")
                print(f"Company: {job.company}")
                print(f"Location: {job.location}")
                print(f"Employment Type: {job.employment_type}")
                print(f"Source: {job.source}")
                print(f"URL: {job.url}")

                print("\nMatch:")
                print(f"  Score: {job.match.score}")

                print(
                    "  Matching Skills: "
                    f"{', '.join(job.match.matching_skills)}"
                )

                print(
                    "  Missing Skills: "
                    f"{', '.join(job.match.missing_skills)}"
                )

                print(
                    f"  Explanation: {job.match.explanation}"
                )

    except Exception as e:

        print("\nJOB AGENT ERROR")
        print("-" * 70)
        print(type(e).__name__)
        print(str(e))

    # ============================================================
    # 2. TEST FREELANCER AGENT
    # ============================================================

    print("\n\n" + "=" * 70)
    print("2. TESTING FREELANCER AGENT")
    print("=" * 70)

    try:
        freelance_result = freelance_agent(test_state)

        projects = freelance_result.get(
            "freelance_projects",
            []
        )

        if not projects:
            print("\nNo freelance projects returned.")

        else:
            print(
                f"\nFound {len(projects)} freelance project(s).\n"
            )

            for i, project in enumerate(projects, start=1):

                print("-" * 70)
                print(f"FREELANCE PROJECT #{i}")

                print(f"Title: {project.title}")
                print(f"Source: {project.source}")
                print(f"URL: {project.url}")
                print(f"Budget/Rate: {project.budget}")

                print("\nMatch:")
                print(f"  Score: {project.match_score}")

                print(
                    "  Matching Skills: "
                    f"{', '.join(project.matching_skills)}"
                )

                print(
                    "  Missing Skills: "
                    f"{', '.join(project.missing_skills)}"
                )

                print(
                    f"  Explanation: {project.explanation}"
                )

    except Exception as e:

        print("\nFREELANCER AGENT ERROR")
        print("-" * 70)
        print(type(e).__name__)
        print(str(e))

    # ============================================================
    # 3. TEST CERTIFICATION AGENT
    # ============================================================

    print("\n\n" + "=" * 70)
    print("3. TESTING CERTIFICATION AGENT")
    print("=" * 70)

    try:
        certification_result = certification_agent(test_state)

        analysis = certification_result.get(
            "certification_analysis",
            ""
        )

        if not analysis:
            print("\nNo certification analysis returned.")

        else:
            print("\nCERTIFICATION ANALYSIS:\n")
            print(analysis)

    except Exception as e:

        print("\nCERTIFICATION AGENT ERROR")
        print("-" * 70)
        print(type(e).__name__)
        print(str(e))

    # ============================================================
    # DONE
    # ============================================================

    print("\n\n" + "=" * 70)
    print("ALL AGENTS TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
