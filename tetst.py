from backend.agents.freelance_agent import freelance_agent


# ============================================================
# Test User Profile
# ============================================================

test_state = {
    "user_profile": {
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "JavaScript",
            "SQL",
            "Git",
            "LangChain",
            "RAG",
            "OpenAI"
        ],

        "experience": [
            "Software Engineering graduate",
            "React web development internship",
            "AI and RAG projects",
            "Agentic AI Engineering bootcamp"
        ],

        "interests": [
            "AI",
            "Generative AI",
            "Agentic AI",
            "Web Development",
            "Backend Development"
        ],

        "location": "Saudi Arabia"
    },

    "query": "Find freelance projects related to AI, Python, FastAPI, LangChain, RAG, or React that match my skills."
}


# ============================================================
# Run Agent
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("TESTING FREELANCER AGENT")
    print("=" * 70)

    try:

        result = freelance_agent(test_state)

        print("\n" + "=" * 70)
        print("FREELANCE ANALYSIS")
        print("=" * 70)

        print(result["freelance_analysis"])

    except Exception as e:

        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)

        print(type(e).__name__)
        print(str(e))
