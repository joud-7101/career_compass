from pathlib import Path
import streamlit as st
import requests


# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Dashboard | CareerCompass",
    page_icon=":material/explore:",
    layout="wide"
)


# ---------------------------------
# Assets & config
# ---------------------------------

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")

logo = ASSETS / "logo.png"

API_BASE = "http://127.0.0.1:8000"


# ---------------------------------
# Auth guard — must be signed in
# ---------------------------------

token = st.session_state.get("token")

if not token:
    st.warning("Please sign in to view your dashboard.")

    col1, col2, _ = st.columns([1, 1, 3])

    with col1:
        if st.button("Sign in", type="primary", use_container_width=True):
            st.switch_page("pages/sign_in.py")

    with col2:
        if st.button("Create account", use_container_width=True):
            st.switch_page("pages/sign_up.py")

    st.stop()


# ---------------------------------
# Load profile
# Priority: session state → fresh /me call
# ---------------------------------

profile = st.session_state.get("profile")

if profile is None and token:
    try:
        with st.spinner("Loading your profile..."):
            me_response = requests.get(
                f"{API_BASE}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )

        if me_response.status_code == 200:
            me_data = me_response.json()
            st.session_state["user_email"] = me_data.get("email", "")
            st.session_state["user_id"] = me_data.get("id")

            if me_data.get("profile"):
                profile = me_data["profile"]
                st.session_state["profile"] = profile

    except requests.RequestException:
        pass   # Show dashboard with empty profile — not fatal


# ---------------------------------
# Extract display values from profile
# ---------------------------------

user_email = st.session_state.get("user_email", "")

if profile:
    personal = profile.get("personal_information", {})
    display_name = personal.get("name") or user_email.split("@")[0].title()
    initials = "".join(
        part[0].upper()
        for part in display_name.split()
        if part
    )[:2] or "U"

    # Current role — first experience entry
    experience_list = profile.get("experience", [])
    current_role_title = ""
    current_role_years = ""
    if experience_list:
        current_role_title = experience_list[0].get("title", "")
        start = experience_list[0].get("start_date", "")
        end = experience_list[0].get("end_date", "") or "Present"
        if start:
            current_role_years = f"{start} – {end}"

    # Core skills — first 5
    skills_list = [s.get("name", "") for s in profile.get("skills", [])]
    top_skills = skills_list[:5]

    # Education — first entry
    education_list = profile.get("education", [])
    edu_degree = ""
    edu_institution = ""
    if education_list:
        edu = education_list[0]
        parts = [edu.get("degree", ""), edu.get("field_of_study", "")]
        edu_degree = " in ".join(p for p in parts if p) or "Degree"
        edu_institution = edu.get("institution", "")

else:
    display_name = user_email.split("@")[0].title() if user_email else "there"
    initials = display_name[0].upper() if display_name else "U"
    current_role_title = ""
    current_role_years = ""
    top_skills = []
    edu_degree = ""
    edu_institution = ""


# =================================
# 1. NAVIGATION BAR
# =================================

with st.container(
    key="dash_nav",
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center"
):
    st.image(logo, width=170)

    # Nav links — rendered as styled HTML tabs
    st.html(
        """
        <nav class="cc-navlinks">
            <a class="active" href="#">Dashboard</a>
            <a href="#">Jobs</a>
            <a href="#">Freelance</a>
            <a href="#">Certifications</a>
            <a href="#">Profile</a>
        </nav>
        """
    )

    # Avatar circle with initials
    st.html(
        f"""
        <div class="cc-avatar" title="{display_name}">
            {initials}
        </div>
        """
    )


# =================================
# 2. HERO / WELCOME BANNER
# =================================

with st.container(key="dash_hero"):

    left, right = st.columns([2, 1], vertical_alignment="center")

    with left:
        st.html('<p class="cc-dashboard-eyebrow">YOUR CAREER, IN FOCUS</p>')
        st.html(
            f'<h1 class="cc-dashboard-title">Welcome back, {display_name}.</h1>'
        )
        st.html(
            '<p class="cc-dashboard-subtitle">'
            "Explore career options selected based on your profile."
            "</p>"
        )

    with right:
        with st.container(horizontal_alignment="right"):
            if st.button(
                "Sample profile & recommendations",
                key="sample_profile_btn",
                type="secondary"
            ):
                pass   # future feature


# =================================
# 3. CAREER PROFILE CARD
# =================================

with st.container(
    key="dash_profile_card",
    border=True
):

    header_left, header_right = st.columns(
        [4, 1],
        vertical_alignment="center"
    )

    with header_left:
        st.html(
            f"""
            <div class="cc-profile-header">
                <div class="cc-profile-avatar">{initials}</div>
                <div>
                    <div class="cc-profile-card-title">Your career profile</div>
                    <div class="cc-profile-card-sub">
                        A snapshot of the experience you bring
                    </div>
                </div>
            </div>
            """
        )

    with header_right:
        if st.button(
            "View profile",
            key="view_profile_btn",
            type="secondary"
        ):
            st.switch_page("pages/profile_review.py")

    # Three info columns
    col_role, col_skills, col_edu = st.columns(3)

    with col_role:
        st.html(
            f"""
            <div class="cc-profile-section">
                <p class="cc-profile-label">CURRENT ROLE</p>
                <p class="cc-profile-value">
                    {current_role_title or "—"}
                </p>
                <p class="cc-profile-detail">
                    {current_role_years}
                </p>
            </div>
            """
        )

    with col_skills:
        badges_html = "".join(
            f'<span class="cc-skill-badge">{s}</span>'
            for s in top_skills
        ) if top_skills else "<span>No skills added yet</span>"

        st.html(
            f"""
            <div class="cc-profile-section">
                <p class="cc-profile-label">CORE SKILLS</p>
                <div class="cc-skill-badges">{badges_html}</div>
            </div>
            """
        )

    with col_edu:
        st.html(
            f"""
            <div class="cc-profile-section">
                <p class="cc-profile-label">EDUCATION</p>
                <p class="cc-profile-value">{edu_degree or "—"}</p>
                <p class="cc-profile-detail">{edu_institution}</p>
            </div>
            """
        )


# =================================
# 4. FEATURE CARDS
# =================================

cards = [
    {
        "key": "dash_card_jobs",
        "icon": "description",
        "title": "Jobs",
        "description": "Find roles that fit your skills and experience.",
        "link_label": "View jobs",
        "page": "pages/jobs.py",
    },
    {
        "key": "dash_card_freelance",
        "icon": "hub",
        "title": "Freelance",
        "description": "Put your expertise to work on the right projects.",
        "link_label": "View projects",
        "page": "pages/freelance.py",
    },
    {
        "key": "dash_card_certs",
        "icon": "menu_book",
        "title": "Certifications",
        "description": "Make your next qualification a clear, achievable plan.",
        "link_label": "Create study plan",
        "page": "pages/certifications.py",
    },
]

cols = st.columns(3, gap="medium")

for i, card in enumerate(cards):
    with cols[i]:
        with st.container(
            border=True,
            key=card["key"],
            height="stretch"
        ):
            # Icon
            with st.container(
                key=f"dash_card_icon_{i}",
                width=40
            ):
                st.markdown(f":material/{card['icon']}:")

            st.subheader(card["title"])

            st.write(card["description"])

            if st.button(
                card["link_label"],
                key=f"dash_card_btn_{i}",
                type="tertiary",
                icon=":material/arrow_outward:"
            ):
                if card.get("page"):
                    st.switch_page(card["page"])
                else:
                    st.info(
                        f"{card['title']} is coming soon. "
                        "Your profile is ready!"
                    )


# =================================
# 5. SIGN OUT (footer area)
# =================================

with st.container(key="dash_footer"):

    st.divider()

    _, sign_out_col = st.columns([5, 1])

    with sign_out_col:
        if st.button(
            "Sign out",
            key="signout_btn",
            type="tertiary",
            icon=":material/logout:"
        ):
            # Clear session
            for key in ["token", "user_email", "user_id", "profile",
                        "portfolio_profile", "cv_uploaded", "cv_name"]:
                st.session_state.pop(key, None)

            st.switch_page("app.py")
