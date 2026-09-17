from pathlib import Path
import streamlit as st
import requests

# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Freelance | CareerCompass",
    page_icon=":material/hub:",
    layout="wide"
)

ASSETS = Path(__file__).resolve().parents[1] / "assets"
st.html(ASSETS / "home.css")
logo = ASSETS / "logo.png"
API_BASE = "http://127.0.0.1:8000"


# ---------------------------------
# Auth guard
# ---------------------------------

token = st.session_state.get("token")
if not token:
    st.warning("Please sign in to view your freelance recommendations.")
    if st.button("Sign in", type="primary"):
        st.switch_page("pages/sign_in.py")
    st.stop()


# =================================
# NAVBAR
# =================================

with st.container(
    key="freelance_nav",
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center"
):
    st.image(logo, width=170)

    st.html(
        """
        <nav class="cc-navlinks">
            <a href="#">Dashboard</a>
            <a href="#">Jobs</a>
            <a class="active" href="#">Freelance</a>
            <a href="#">Certifications</a>
            <a href="#">Profile</a>
        </nav>
        """
    )

    if st.button("← Dashboard", key="fl_nav_back", type="tertiary"):
        st.switch_page("pages/dashboard.py")


# =================================
# HEADER
# =================================

with st.container(key="freelance_hero"):

    left, right = st.columns([2, 1], vertical_alignment="center")

    with left:
        st.html('<p class="cc-dashboard-eyebrow">SELECTED FOR YOUR EXPERIENCE</p>')
        st.html('<h1 class="cc-dashboard-title">Freelance projects for you.</h1>')
        st.html(
            '<p class="cc-dashboard-subtitle">'
            "Projects selected based on your skills and professional experience."
            "</p>"
        )

    with right:
        with st.container(horizontal_alignment="right"):
            st.button(
                "Sample profile & recommendations",
                key="fl_sample_btn",
                type="secondary"
            )


# =================================
# FETCH FREELANCE FROM AGENT
# =================================

profile = st.session_state.get("profile", {})
skills_list = [s.get("name", "") for s in (profile.get("skills", []) if profile else [])]
personal = profile.get("personal_information", {}) if profile else {}
display_name = personal.get("name", "") or st.session_state.get("user_email", "").split("@")[0].title()

if "freelance_results" not in st.session_state:
    with st.spinner("🔍 Finding freelance projects matched to your skills..."):
        try:
            resp = requests.post(
                f"{API_BASE}/api/career/freelance",
                json={"query": "Find freelance projects that match my skills"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=120,
            )

            if resp.status_code == 200:
                data = resp.json()
                st.session_state["freelance_results"] = data.get("freelance_projects", [])
                st.session_state["freelance_analysis"] = data.get("analysis", "")
            else:
                st.session_state["freelance_results"] = []
                st.session_state["freelance_analysis"] = ""
                st.error(f"Agent error (status {resp.status_code})")

        except requests.Timeout:
            st.session_state["freelance_results"] = []
            st.session_state["freelance_analysis"] = ""
            st.error("The freelance agent took too long. Please refresh.")

        except requests.RequestException as e:
            st.session_state["freelance_results"] = []
            st.session_state["freelance_analysis"] = ""
            st.error(f"Could not reach the API: {e}")


projects = st.session_state.get("freelance_results", [])
analysis = st.session_state.get("freelance_analysis", "")


# Refresh button
if st.button(
    ":material/refresh: Refresh projects",
    key="fl_refresh",
    type="tertiary"
):
    for key in ["freelance_results", "freelance_analysis"]:
        st.session_state.pop(key, None)
    st.rerun()

# =================================
# PROJECT CARDS — 2-column grid
# =================================

if not projects and not analysis:
    st.info(
        "No freelance projects found. Try refreshing or make sure your "
        "profile has skills added."
    )

if projects:
    # Render in pairs (2-column grid)
    for row_start in range(0, len(projects), 2):
        row_projects = projects[row_start: row_start + 2]
        cols = st.columns(len(row_projects), gap="medium")

        for col_idx, (col, project) in enumerate(zip(cols, row_projects)):

            # Unique index for EVERY project
            project_index = row_start + col_idx

            with col:
                title = project.get("title", "Untitled Project")
                category = project.get("category", project.get("skills", ""))
                description = project.get("description", "")
                budget = project.get(
                    "budget",
                    project.get("budget_or_rate", "")
                )
                duration = project.get("duration", "")
                project_url = project.get(
                    "url",
                    project.get("job_url", "")
                )
                match_score = project.get("match_score", "")
                project_skills = project.get("skills", [])

                # ---------------------------------
                # Skills
                # ---------------------------------

                if isinstance(project_skills, list):
                    project_skill_names = [
                        str(s) for s in project_skills if s
                    ][:4]
                else:
                    project_skill_names = []

                # ---------------------------------
                # Category
                # ---------------------------------

                if isinstance(category, list):
                    category_str = ", ".join(
                        str(c) for c in category[:2]
                    )
                else:
                    category_str = str(category) if category else ""

                # ---------------------------------
                # PROJECT CARD
                # ---------------------------------

                with st.container(
                    key=f"fl_card_{project_index}",
                    border=True
                ):

                    # Top row: icon + match badge
                    top_l, top_r = st.columns(
                        [3, 1],
                        vertical_alignment="center"
                    )

                    with top_l:
                        st.markdown(":material/arrow_outward:")

                    with top_r:
                        if match_score:
                            st.html(
                                f"""
                                <div class="cc-match-badge">
                                    {match_score}% match
                                </div>
                                """
                            )

                    # ---------------------------------
                    # Title + category
                    # ---------------------------------

                    st.html(
                        f"""
                        <div class="cc-profile-value"
                             style="font-size:17px; margin:4px 0 2px;">
                            {title}
                        </div>

                        <div class="cc-profile-detail"
                             style="margin:0 0 10px;">
                            {category_str}
                        </div>
                        """
                    )

                    # ---------------------------------
                    # Description
                    # ---------------------------------

                    if description:
                        snippet = description[:180].strip()

                        if len(description) > 180:
                            snippet += "…"

                        st.write(snippet)

                    # ---------------------------------
                    # Skill badges
                    # ---------------------------------

                    if project_skill_names:
                        badges = "".join(
                            f'<span class="cc-skill-badge">{s}</span>'
                            for s in project_skill_names
                        )

                        st.html(
                            f"""
                            <div class="cc-skill-badges"
                                 style="margin:6px 0;">
                                {badges}
                            </div>
                            """
                        )

                    # ---------------------------------
                    # Budget + Duration
                    # ---------------------------------

                    meta_l, meta_r = st.columns(2)

                    with meta_l:
                        if budget:
                            st.html(
                                f"""
                                <div class="cc-meta-label">
                                    PROJECT BUDGET
                                </div>
                                <div class="cc-meta-value">
                                    {budget}
                                </div>
                                """
                            )

                    with meta_r:
                        if duration:
                            st.html(
                                f"""
                                <div class="cc-meta-label">
                                    DURATION
                                </div>
                                <div class="cc-meta-value">
                                    {duration}
                                </div>
                                """
                            )

                    # ---------------------------------
                    # Why it matches
                    # ---------------------------------

                    matching = (
                        ", ".join(skills_list[:3])
                        if skills_list
                        else "your skills"
                    )

                    st.html(
                        f"""
                        <div class="cc-why-matches"
                             style="margin:10px 0;">

                            <div class="cc-why-title">
                                Why it matches you
                            </div>

                            <div class="cc-why-text">
                                Your {matching} experience
                                match the main project requirements.
                            </div>

                        </div>
                        """
                    )

                    # ---------------------------------
                    # Buttons
                    # ---------------------------------

                    btn_view, btn_save = st.columns(2)

                    # VIEW
                    with btn_view:
                        if project_url:
                            st.link_button(
                                "View project ↗",
                                url=str(project_url),
                                type="primary",
                                use_container_width=True
                            )
                        else:
                            st.button(
                                "View project ↗",
                                key=f"fl_view_{project_index}",
                                type="primary",
                                use_container_width=True,
                                disabled=True
                            )

                    # SAVE
                    with btn_save:
                        st.button(
                            "Save project",
                            key=f"fl_save_{project_index}",
                            use_container_width=True
                        )

# --- If no structured projects but analysis text exists ---
if not projects and analysis:
    st.subheader("Agent Recommendations")
    st.markdown(analysis)
