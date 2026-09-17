from pathlib import Path
import streamlit as st
import requests


# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Create Account | CareerCompass",
    page_icon="🧭",
    layout="wide"
)


# ---------------------------------
# Assets
# ---------------------------------

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")

logo = ASSETS / "logo.png"

API_BASE = "http://127.0.0.1:8000"


# ---------------------------------
# Page layout
# ---------------------------------

left, center, right = st.columns(
    [1, 1.3, 1]
)


with center:

    # Logo
    st.image(
        logo,
        width=180
    )

    # Title
    st.title(
        "Create your account"
    )

    st.write(
        "Start your CareerCompass journey."
    )


    # ---------------------------------
    # Form
    # ---------------------------------

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm password",
        type="password"
    )


    # ---------------------------------
    # Create account button
    # ---------------------------------

    if st.button(
        "Create Account",
        type="primary",
        use_container_width=True
    ):

        # Check empty fields
        if (
            not email
            or not password
            or not confirm_password
        ):
            st.warning(
                "Please complete all fields."
            )

        # Check passwords
        elif password != confirm_password:
            st.error(
                "Passwords do not match."
            )

        elif len(password) < 8:
            st.error(
                "Password must be at least 8 characters."
            )

        # Everything is correct — call register API
        else:
            try:
                with st.spinner("Creating your account..."):
                    response = requests.post(
                        f"{API_BASE}/api/auth/register",
                        json={
                            "email": email,
                            "password": password,
                        },
                        timeout=15,
                    )

                if response.status_code == 201:
                    data = response.json()

                    # Store auth token and user email
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user_email"] = email

                    # Go to CV upload page
                    st.switch_page("pages/upload_cv.py")

                elif response.status_code == 400:
                    detail = response.json().get("detail", "")
                    if "already registered" in detail:
                        st.error(
                            "An account with this email already exists. "
                            "Please sign in instead."
                        )
                    else:
                        st.error(f"Registration failed: {detail}")

                else:
                    st.error(
                        f"Registration failed (status {response.status_code}). "
                        "Please try again."
                    )

            except requests.Timeout:
                st.error(
                    "The server is taking too long to respond. "
                    "Please try again."
                )

            except requests.RequestException as e:
                st.error(
                    f"Could not connect to CareerCompass API: {e}"
                )


    # ---------------------------------
    # Sign in link
    # ---------------------------------

    st.divider()

    st.write(
        "Already have an account?"
    )

    if st.button(
        "Sign in",
        use_container_width=True
    ):
        st.switch_page("pages/sign_in.py")