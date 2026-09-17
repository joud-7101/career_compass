from pathlib import Path
import streamlit as st
from components.portfolio import portfolio_section
import requests

# -----------------------------
# Page settings
# -----------------------------

st.set_page_config(
    page_title="Upload CV | CareerCompass",
    page_icon="🧭",
    layout="wide"
)


# -----------------------------
# Assets
# -----------------------------

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")


# -----------------------------
# Page
# -----------------------------

left, center, right = st.columns(
    [1, 1.4, 1]
)


with center:

    st.image(
        ASSETS / "logo.png",
        width=180
    )

    st.title("Upload your CV")

    st.write(
        "Upload your CV so CareerCompass can "
        "extract your profile information automatically."
    )


    # -------------------------
    # Upload CV
    # -------------------------

    cv_file = st.file_uploader(
        "Choose your CV",
        type=["pdf", "docx"]
    )


    if cv_file is not None:

        st.success(
            f"{cv_file.name} uploaded successfully."
        )

        st.session_state["cv_name"] = cv_file.name
        st.session_state["cv_uploaded"] = True


        # portfolio
        st.divider()
        portfolio_url = portfolio_section()


        if st.button("Continue", type="primary", use_container_width=True):
            if portfolio_url:
                try:
                    with st.spinner("Extracting your portfolio..."):
                        response = requests.post(
                            "http://127.0.0.1:8000/api/users/me/portfolio",
                            json={"url": portfolio_url},
                            timeout=60,
                        )

                    if response.status_code == 200:
                        data = response.json()

                        # Save extracted portfolio profile
                        st.session_state["portfolio_profile"] = data["profile"]["profile"]

                        # Save extraction warnings
                        st.session_state["portfolio_warnings"] = data["profile"].get(
                            "extraction_warnings", []
                        )

                        # Go to Profile Review
                        st.switch_page("pages/profile_review.py")

                    else:
                        st.error(
                            f"Portfolio extraction failed. "
                            f"Status: {response.status_code}"
                        )
                        st.code(response.text)

                except requests.Timeout:
                    st.error(
                        "Portfolio extraction is taking too long. "
                        "Please try again."
                    )

                except requests.RequestException as e:
                    st.error(f"Could not connect to the CareerCompass API: {e}")

            else:
                st.info("No portfolio URL added. You can continue without one.")