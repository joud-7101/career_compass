from backend.graph.state import CareerState
from backend.agents.job_agent import job_agent


def main():
    # Test user profile
    test_state: CareerState = {
        "user_profile": {
            "name": "Joud",
            "education": "BSc Software Engineering",
            "experience": [
                "Software Engineering Intern at Sallam Tech"
            ],
            "skills": [
                "Python",
                "JavaScript",
                "React",
                "HTML",
                "CSS",
                "FastAPI",
                "RAG",
                "LLMs",
                "Git"
            ],
            "interests": [
                "Artificial Intelligence",
                "Software Engineering",
                "Web Development"
            ],
            "location": "Saudi Arabia"
        },

        "query": "Find entry-level AI Engineer and Software Engineer jobs in Saudi Arabia"
    }

    print("=" * 70)
    print("TESTING JOB AGENT")
    print("=" * 70)

    try:
        result = job_agent(test_state)

        print("\n" + "=" * 70)
        print("JOB AGENT RESULT")
        print("=" * 70)

        print(result.get("job_analysis", "No job analysis returned."))

    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)

        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    main()
