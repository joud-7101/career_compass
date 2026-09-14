from pathlib import Path
import streamlit as st


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


        if st.button(
            "Continue",
            type="primary",
            use_container_width=True
        ):

            st.info(
                "Next: extract the CV data and create the profile."
            )