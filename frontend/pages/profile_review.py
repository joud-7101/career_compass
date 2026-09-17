import streamlit as st
from pathlib import Path

from components.profile import render_profile_editor


st.set_page_config(
    page_title="Profile Review | CareerCompass",
    page_icon="🧭",
    layout="wide",
)

ASSETS = Path(__file__).resolve().parents[1] / "assets"
st.html(ASSETS / "home.css")


# --------------------------------------------------
# Load profile
# --------------------------------------------------

profile_data = st.session_state.get("profile")

# Temporary fallback:
# until CV + Portfolio are merged, use the portfolio extraction.
if profile_data is None:
    profile_data = st.session_state.get("portfolio_profile")


if profile_data is None:
    st.warning("No extracted profile is available yet.")
    st.info("Please upload your CV or add your portfolio first.")
    st.stop()


# --------------------------------------------------
# Header
# --------------------------------------------------

left, center, right = st.columns([1, 1.5, 1])

with center:
    st.image(ASSETS / "logo.png", width=160)

    st.title("Review Your Profile")
    st.write(
        "We've extracted the following information from your documents "
        "and portfolio. Please review and edit it before continuing."
    )


# --------------------------------------------------
# Extraction warnings
# --------------------------------------------------

warnings = st.session_state.get("portfolio_warnings", [])

if warnings:
    with st.expander("Extraction notes"):
        for warning in warnings:
            st.write(f"• {warning}")


# --------------------------------------------------
# Profile editor
# --------------------------------------------------

with center:
    updated_profile = render_profile_editor(profile_data)


if updated_profile:
    st.session_state["profile"] = updated_profile.model_dump(
        mode="json"
    )

    st.switch_page("app.py")