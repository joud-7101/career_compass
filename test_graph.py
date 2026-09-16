from backend.graph.graph import career_graph


test_state = {
    "user_id": "1",
    "query": "Find data analysis jobs, relevant certifications, and freelance opportunities",
    "user_profile": {
        "name": "Test User",
        "education": "Computer Science",
        "experience": ["Beginner"],
        "skills": ["Python", "Excel", "Data Analysis"],
        "interests": ["Data Analysis"],
        "location": "Saudi Arabia",
    },
}


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING CAREER GRAPH")
    print("=" * 70)

    try:
        result = career_graph.invoke(test_state)

        print("\nREQUESTED AGENTS:")
        print(result.get("requested_agents"))

        print("\nJOB ANALYSIS:")
        print(result.get("job_analysis", "No job result"))

        print("\nCERTIFICATION ANALYSIS:")
        print(result.get("certification_analysis", "No certification result"))

        print("\nFREELANCE ANALYSIS:")
        print(result.get("freelance_analysis", "No freelance result"))

        print("\nFINAL RESPONSE:")
        print(result.get("final_response", "No final response"))

    except Exception as e:
        print("\nERROR:")
        print(type(e).__name__)
        print(str(e)) 
        print("\nSTRUCTURED JOBS:")
print(result.get("jobs", []))

print("\nSTRUCTURED CERTIFICATIONS:")
print(result.get("certifications", []))

print("\nSTRUCTURED FREELANCE PROJECTS:")
print(result.get("freelance_projects", [])) 