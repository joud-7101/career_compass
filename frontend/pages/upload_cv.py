from pathlib import Path

import requests
import streamlit as st

from components.portfolio import portfolio_section


# --------------------------------------------------
# Page settings
# --------------------------------------------------

st.set_page_config(
    page_title="Upload CV | CareerCompass",
    page_icon="🧭",
    layout="wide",
)


# --------------------------------------------------
# Assets
# --------------------------------------------------

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")


# --------------------------------------------------
# Page layout
# --------------------------------------------------

left, center, right = st.columns(
    [1, 1.4, 1]
)


with center:

    st.image(
        ASSETS / "logo.png",
        width=180,
    )

    st.title("Upload your CV")

    st.write(
        "Upload your CV so CareerCompass can "
        "extract your profile information automatically."
    )


    # --------------------------------------------------
    # CV Upload
    # --------------------------------------------------

    cv_file = st.file_uploader(
        "Choose your CV",
        type=["pdf"],
    )


    if cv_file is not None:

        # File is selected, but not uploaded yet
        st.success(
            f"{cv_file.name} selected successfully."
        )

        st.session_state["cv_name"] = cv_file.name


        # --------------------------------------------------
        # Get authentication token
        # --------------------------------------------------

        token = st.session_state.get("token")


        # --------------------------------------------------
        # Upload CV button
        # --------------------------------------------------

        upload_button = st.button(
            "Upload CV",
            type="primary",
            use_container_width=True,
        )


        # --------------------------------------------------
        # Retry button
        # Show only if the previous upload failed
        # --------------------------------------------------

        retry_button = False

        if st.session_state.get(
            "cv_upload_failed",
            False,
        ):

            st.error(
                st.session_state.get(
                    "cv_upload_error",
                    "Failed to upload CV.",
                )
            )

            retry_button = st.button(
                "Retry",
                use_container_width=True,
            )


        # --------------------------------------------------
        # Send CV to FastAPI
        # --------------------------------------------------

        if upload_button or retry_button:

            # User must be logged in
            if not token:

                st.error(
                    "Your session has expired. "
                    "Please log in again."
                )

                st.stop()


            # Prepare PDF file for the API request
            files = {
                "file": (
                    cv_file.name,
                    cv_file.getvalue(),
                    "application/pdf",
                )
            }


            try:

                with st.spinner(
                    "Uploading and processing your CV..."
                ):

                    response = requests.post(
                        "http://127.0.0.1:8000/api/users/me/resume",
                        files=files,
                        headers={
                            "Authorization": f"Bearer {token}"
                        },
                        timeout=60,
                    )


                # --------------------------------------------------
                # CV successfully processed
                # --------------------------------------------------

                if response.status_code == 200:

                    data = response.json()

                    st.session_state["cv_uploaded"] = True
                    st.session_state["cv_upload_failed"] = False

                    # Save extracted CV profile
                    # Profile Review page will use this data
                    st.session_state["profile"] = data["profile"]

                    st.success(
                        "CV uploaded and processed successfully."
                    )


                # --------------------------------------------------
                # Backend returned an error
                # --------------------------------------------------

                else:

                    st.session_state["cv_upload_failed"] = True

                    st.session_state["cv_upload_error"] = (
                        "Failed to upload CV. "
                        "Please try again."
                    )

                    st.error(
                        st.session_state["cv_upload_error"]
                    )


            # --------------------------------------------------
            # Could not connect to FastAPI
            # --------------------------------------------------

            except requests.exceptions.RequestException:

                st.session_state["cv_upload_failed"] = True

                st.session_state["cv_upload_error"] = (
                    "Could not connect to the server. "
                    "Please try again."
                )

                st.error(
                    st.session_state["cv_upload_error"]
                )


        # --------------------------------------------------
        # Portfolio
        # Optional extra source
        # --------------------------------------------------

        st.divider()

        portfolio_url = portfolio_section()


        # --------------------------------------------------
        # Continue to Profile Review
        # --------------------------------------------------

        if st.button(
            "Continue",
            type="primary",
            use_container_width=True,
        ):

            # CV must be processed first
            if not st.session_state.get(
                "cv_uploaded",
                False,
            ):

                st.warning(
                    "Please upload and process your CV first."
                )


            # --------------------------------------------------
            # Portfolio URL was provided
            # --------------------------------------------------

            elif portfolio_url:

                try:

                    with st.spinner(
                        "Extracting your portfolio..."
                    ):

                        response = requests.post(
                            "http://127.0.0.1:8000/api/users/me/portfolio",
                            json={
                                "url": portfolio_url
                            },
                            headers={
                                "Authorization": f"Bearer {token}"
                            },
                            timeout=60,
                        )


                    # Portfolio successfully processed
                    if response.status_code == 200:

                        data = response.json()

                        # Save extracted portfolio profile
                        st.session_state["portfolio_profile"] = (
                            data["profile"]["profile"]
                        )

                        # Save extraction warnings
                        st.session_state["portfolio_warnings"] = (
                            data["profile"].get(
                                "extraction_warnings",
                                [],
                            )
                        )

                        # Go to Profile Review
                        st.switch_page(
                            "pages/profile_review.py"
                        )


                    # Portfolio backend error
                    else:

                        st.error(
                            "Portfolio extraction failed. "
                            f"Status: {response.status_code}"
                        )

                        st.code(
                            response.text
                        )


                except requests.Timeout:

                    st.error(
                        "Portfolio extraction is taking too long. "
                        "Please try again."
                    )


                except requests.RequestException as e:

                    st.error(
                        "Could not connect to the "
                        f"CareerCompass API: {e}"
                    )


            # --------------------------------------------------
            # No portfolio URL
            # Portfolio is optional, continue with CV only
            # --------------------------------------------------

            else:

                st.switch_page(
                    "pages/profile_review.py"
                )