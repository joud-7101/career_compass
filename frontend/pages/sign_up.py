"""from pathlib import Path
import streamlit as st


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

    first_name = st.text_input(
        "First name"
    )

    last_name = st.text_input(
        "Last name"
    )

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
            not first_name
            or not last_name
            or not email
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


        # Everything is correct
        else:

            # Save user data temporarily
            st.session_state["user"] = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }

            # Go to CV upload page
            st.switch_page(
                "pages/upload_cv.py"
            )


    # ---------------------------------
    # Sign in
    # ---------------------------------

    st.divider()

    st.write(
        "Already have an account?"
    )

    if st.button(
        "Sign in",
        use_container_width=True
    ):

        st.info(
            "Sign in page will be connected next."
        )"""

from pathlib import Path

import streamlit as st


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
    # Sign up form
    # ---------------------------------

    with st.form("signup_form"):

        first_name = st.text_input(
            "First name"
        )

        last_name = st.text_input(
            "Last name"
        )

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

        create_account = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True
        )


    # ---------------------------------
    # Validate form
    # ---------------------------------

    if create_account:

        # Check empty fields
        if (
            not first_name.strip()
            or not last_name.strip()
            or not email.strip()
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


        # Everything is correct
        else:

            # Save user data temporarily
            st.session_state["user"] = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email.strip()
            }

            # Go to CV upload page
            st.switch_page(
                "pages/upload_cv.py"
            )


    # ---------------------------------
    # Sign in
    # ---------------------------------

    st.divider()

    st.write(
        "Already have an account?"
    )

    if st.button(
        "Sign in",
        use_container_width=True
    ):

        st.info(
            "Sign in page will be connected next."
        )