import streamlit as st
import requests


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Career Compass",
    page_icon="🧭"
)


st.title("🧭 Career Compass")

st.subheader("Your AI Career Assistant")


user_id = st.text_input(
    "User ID",
    value="user_001"
)


query = st.text_area(
    "What do you need help with?",
    placeholder=(
        "Example: Find me software engineering "
        "jobs and certifications."
    )
)


if st.button("Ask Career Compass"):

    if not query:

        st.warning(
            "Please enter your career question."
        )

    else:

        with st.spinner(
            "Career Compass is working..."
        ):

            response = requests.post(
                f"{API_URL}/api/career",
                json={
                    "user_id": user_id,
                    "query": query
                }
            )

        if response.status_code == 200:

            data = response.json()

            st.success(
                "Career analysis completed."
            )

            st.write(
                data["response"]
            )

            if data["jobs"]:

                st.subheader(
                    "💼 Jobs"
                )

                for job in data["jobs"]:

                    st.write(
                        f"**{job['title']}**"
                    )

                    st.write(
                        job["company"]
                    )

            if data["certifications"]:

                st.subheader(
                    "🎓 Certifications"
                )

                for cert in data[
                    "certifications"
                ]:

                    st.write(
                        f"**{cert['name']}**"
                    )

            if data["freelance_projects"]:

                st.subheader(
                    "💻 Freelance Projects"
                )

                for project in data[
                    "freelance_projects"
                ]:

                    st.write(
                        f"**{project['title']}**"
                    )

        else:

            st.error(
                f"API Error: {response.text}"
            )