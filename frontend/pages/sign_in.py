from pathlib import Path
import streamlit as st


# -----------------------------
# Page settings
# -----------------------------

st.set_page_config(
    page_title="Sign In | CareerCompass",
    page_icon="🧭",
    layout="wide"
)


# -----------------------------
# Assets
# -----------------------------

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")

logo = ASSETS / "logo.png"


# -----------------------------
# Page layout
# -----------------------------

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
        "Welcome back"
    )

    st.write(
        "Sign in to continue to CareerCompass."
    )


    # -------------------------
    # Login form
    # -------------------------

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )


    # -------------------------
    # Sign in button
    # -------------------------

    if st.button(
        "Sign in",
        type="primary",
        use_container_width=True
    ):

        if not email or not password:

            st.warning(
                "Please enter your email and password."
            )

        else:

            # Temporary login
            st.session_state["logged_in"] = True
            st.session_state["email"] = email

            st.switch_page(
                "pages/dashboard.py"
            )


    # -------------------------
    # Create account
    # -------------------------

    st.divider()

    st.write(
        "Don't have an account?"
    )

    if st.button(
        "Create Account",
        use_container_width=True
    ):

        st.switch_page(
            "pages/sign_up.py"
        )