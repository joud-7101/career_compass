from pathlib import Path

import requests
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
        type=["pdf"]
    )


    if cv_file is not None:

        st.success(
            f"{cv_file.name} selected successfully."
        )

        st.session_state["cv_name"] = cv_file.name


        # -------------------------
        # Upload button
        # -------------------------

        upload_button = st.button(
            "Upload CV",
            type="primary",
            use_container_width=True
        )


        # -------------------------
        # Retry button
        # -------------------------

        retry_button = False

        if st.session_state.get(
            "cv_upload_failed",
            False
        ):

            st.error(
                st.session_state.get(
                    "cv_upload_error",
                    "Failed to upload CV."
                )
            )

            retry_button = st.button(
                "Retry",
                use_container_width=True
            )


        # -------------------------
        # Send CV to FastAPI
        # -------------------------

        if upload_button or retry_button:

            files = {
                "file": (
                    cv_file.name,
                    cv_file.getvalue(),
                    "application/pdf"
                )
            }

            try:

                with st.spinner(
                    "Uploading and processing your CV..."
                ):

                    response = requests.post(
                        "http://127.0.0.1:8000/api/users/me/resume",
                        files=files,
                        timeout=60
                    )


                # -------------------------
                # Success
                # -------------------------

                if response.status_code == 200:

                    st.session_state["cv_uploaded"] = True
                    st.session_state["cv_upload_failed"] = False

                    st.success(
                        "CV uploaded successfully."
                    )


                # -------------------------
                # Backend error
                # -------------------------

                else:

                    st.session_state["cv_upload_failed"] = True

                    st.session_state["cv_upload_error"] = (
                        "Failed to upload CV. "
                        "Please try again."
                    )

                    st.rerun()


            # -------------------------
            # Connection error
            # -------------------------

            except requests.exceptions.RequestException:

                st.session_state["cv_upload_failed"] = True

                st.session_state["cv_upload_error"] = (
                    "Could not connect to the server. "
                    "Please try again."
                )

                st.rerun()