from pathlib import Path
import streamlit as st
import requests


# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Sign In | CareerCompass",
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
    st.title("Sign in")

    st.write(
        "Welcome back to CareerCompass."
    )


    # ---------------------------------
    # Form
    # ---------------------------------

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )


    # ---------------------------------
    # Sign in button
    # ---------------------------------

    if st.button(
        "Sign in",
        type="primary",
        use_container_width=True,
        key="signin_btn"
    ):

        if not email or not password:
            st.warning("Please enter your email and password.")

        else:
            try:
                with st.spinner("Signing you in..."):
                    response = requests.post(
                        f"{API_BASE}/api/auth/login",
                        json={
                            "email": email,
                            "password": password,
                        },
                        timeout=15,
                    )

                if response.status_code == 200:
                    data = response.json()
                    token = data["access_token"]

                    # -------------------------------------------
                    # Fetch the user's saved profile from the API
                    # -------------------------------------------
                    me_response = requests.get(
                        f"{API_BASE}/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=15,
                    )

                    if me_response.status_code == 200:
                        me_data = me_response.json()

                        # Store auth info
                        st.session_state["token"] = token
                        st.session_state["user_email"] = me_data["email"]
                        st.session_state["user_id"] = me_data["id"]

                        # Store profile (may be None if not uploaded yet)
                        if me_data.get("profile"):
                            st.session_state["profile"] = me_data["profile"]

                        # Go to dashboard
                        st.switch_page("pages/dashboard.py")

                    else:
                        st.error("Could not load your profile. Please try again.")

                elif response.status_code == 401:
                    st.error(
                        "Invalid email or password. Please try again."
                    )

                else:
                    st.error(
                        f"Sign in failed (status {response.status_code}). "
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
    # Create account link
    # ---------------------------------

    st.divider()

    st.write("Don't have an account?")

    if st.button(
        "Create account",
        use_container_width=True,
        key="go_signup"
    ):
        st.switch_page("pages/sign_up.py")
