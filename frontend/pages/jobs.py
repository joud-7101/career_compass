from pathlib import Path
import streamlit as st
import requests

# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Jobs | CareerCompass",
    page_icon=":material/work:",
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
    st.warning("Please sign in to view your job recommendations.")
    if st.button("Sign in", type="primary"):
        st.switch_page("pages/sign_in.py")
    st.stop()


# =================================
# NAVBAR
# =================================

with st.container(
    key="jobs_nav",
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center"
):
    st.image(logo, width=170)

    st.html(
        """
        <nav class="cc-navlinks">
            <a href="#" onclick="window.location.href='?page=dashboard'">Dashboard</a>
            <a class="active" href="#">Jobs</a>
            <a href="#">Freelance</a>
            <a href="#">Certifications</a>
            <a href="#">Profile</a>
        </nav>
        """
    )

    col_nav_dash, col_nav_blank = st.columns([1, 4])
    with col_nav_dash:
        if st.button("← Dashboard", key="nav_back_dash", type="tertiary"):
            st.switch_page("pages/dashboard.py")


# =================================
# HEADER
# =================================

with st.container(key="jobs_hero"):

    left, right = st.columns([2, 1], vertical_alignment="center")

    with left:
        st.html('<p class="cc-dashboard-eyebrow">SELECTED FOR YOUR EXPERIENCE</p>')
        st.html('<h1 class="cc-dashboard-title">Jobs for you.</h1>')
        st.html(
            '<p class="cc-dashboard-subtitle">'
            "Opportunities selected based on your career profile."
            "</p>"
        )

    with right:
        with st.container(horizontal_alignment="right"):
            st.button(
                "Sample profile & recommendations",
                key="jobs_sample_btn",
                type="secondary"
            )


# =================================
# PROFILE SNAPSHOT CARD
# =================================

profile = st.session_state.get("profile", {})
personal = profile.get("personal_information", {}) if profile else {}
display_name = personal.get("name", "") or st.session_state.get("user_email", "").split("@")[0].title()
initials = "".join(p[0].upper() for p in display_name.split() if p)[:2] or "U"

experience_list = profile.get("experience", []) if profile else []
current_role = experience_list[0].get("title", "—") if experience_list else "—"

skills_list = [s.get("name", "") for s in (profile.get("skills", []) if profile else [])]
top_3_skills = skills_list[:3]

with st.container(key="jobs_profile_card", border=True):

    left_card, right_card = st.columns([3, 1], vertical_alignment="center")

    with left_card:
        skill_badges = "".join(
            f'<span class="cc-skill-badge">{s}</span>'
            for s in top_3_skills
        )
        st.html(
            f"""
            <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
                <div class="cc-profile-avatar" style="width:40px;height:40px;font-size:15px;">{initials}</div>
                <div>
                    <div class="cc-profile-value" style="margin:0;">{current_role}</div>
                    <div class="cc-profile-detail" style="margin:0;">
                        {len(experience_list)} role(s) of experience
                    </div>
                </div>
                <div class="cc-skill-badges" style="margin-left:24px;">{skill_badges}</div>
            </div>
            """
        )

    with right_card:
        if st.button("Update profile ↗", key="jobs_update_profile", type="tertiary"):
            st.switch_page("pages/profile_review.py")


# =================================
# FETCH JOBS FROM AGENT
# =================================

if "jobs_results" not in st.session_state:
    with st.spinner("🔍 Finding job opportunities matched to your profile..."):
        try:
            resp = requests.post(
                f"{API_BASE}/api/career/jobs",
                json={"query": f"Find jobs matching profile of {current_role}"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=120,
            )

            if resp.status_code == 200:
                data = resp.json()
                st.session_state["jobs_results"] = data.get("jobs", [])
                st.session_state["jobs_analysis"] = data.get("analysis", "")
            else:
                st.session_state["jobs_results"] = []
                st.session_state["jobs_analysis"] = ""
                st.error(f"Agent error (status {resp.status_code}): {resp.text[:200]}")

        except requests.Timeout:
            st.session_state["jobs_results"] = []
            st.session_state["jobs_analysis"] = ""
            st.error("The job agent took too long. Please refresh to try again.")
        except requests.RequestException as e:
            st.session_state["jobs_results"] = []
            st.session_state["jobs_analysis"] = ""
            st.error(f"Could not reach the API: {e}")

jobs = st.session_state.get("jobs_results", [])
analysis = st.session_state.get("jobs_analysis", "")


# =================================
# RESULTS HEADER
# =================================

count_col, note_col = st.columns([2, 2])

with count_col:
    st.caption(
        f"Recommended opportunities · {len(jobs)} role{'s' if len(jobs) != 1 else ''}"
    )

with note_col:
    st.caption("Based on your profile")


# =================================
# REFRESH BUTTON
# =================================

if st.button(
    ":material/refresh: Refresh recommendations",
    key="jobs_refresh",
    type="tertiary"
):
    for key in ["jobs_results", "jobs_analysis"]:
        st.session_state.pop(key, None)
    st.rerun()


# =================================
# JOB CARDS
# =================================

if not jobs and not analysis:
    st.info(
        "No jobs found yet. Try refreshing, or make sure your profile "
        "has skills and experience filled in."
    )

# --- Show each job card ---
for i, job in enumerate(jobs):
    title = job.get("title", "Untitled Role")
    company = job.get("company", "")
    location = job.get("location", "")
    job_type = job.get("job_type", "") or job.get("employment_type", "")
    is_remote = job.get("is_remote", False)
    job_url = job.get("job_url", "") or job.get("url", "")
    description = job.get("description", "")
    source = job.get("site", job.get("source", ""))

    company_initial = (company[0].upper() if company else "J")

    # Determine employment type label
    employment_label_parts = []
    if job_type:
        employment_label_parts.append(str(job_type).replace("_", " ").title())
    if is_remote:
        employment_label_parts.append("Remote")
    employment_label = " · ".join(employment_label_parts) if employment_label_parts else "Full-time"

    with st.container(key=f"job_card_{i}", border=True):

        top_left, top_right = st.columns([5, 1], vertical_alignment="top")

        with top_left:
            st.html(
                f"""
                <div style="display:flex; align-items:flex-start; gap:14px;">
                    <div class="cc-job-company-icon">{company_initial}</div>
                    <div>
                        <div class="cc-profile-value" style="font-size:18px; margin:0;">{title}</div>
                        <div class="cc-profile-detail" style="margin:2px 0 0;">
                            {company}{' · ' + location if location else ''}
                        </div>
                    </div>
                </div>
                """
            )

        with top_right:
            st.html('<div class="cc-match-badge">Match</div>')

        # Description snippet
        if description:
            snippet = description[:220].strip()
            if len(description) > 220:
                snippet += "…"
            st.write(snippet)

        # Skill badges from user's matching skills
        if top_3_skills:
            badges = "".join(
                f'<span class="cc-skill-badge">{s}</span>'
                for s in top_3_skills
            )
            st.html(f'<div class="cc-skill-badges" style="margin:4px 0 8px;">{badges}</div>')

        # "Why it matches you" callout — use agent analysis for first card, generic for rest
        if i == 0 and analysis:
            # Use first ~400 chars of agent analysis
            analysis_snippet = analysis[:400].strip()
            if len(analysis) > 400:
                analysis_snippet += "…"
            st.html(
                f"""
                <div class="cc-why-matches">
                    <div class="cc-why-title">Why it matches you</div>
                    <div class="cc-why-text">{analysis_snippet}</div>
                </div>
                """
            )
        else:
            # Generic match reason
            matched = ", ".join(top_3_skills[:3]) if top_3_skills else "your profile"
            st.html(
                f"""
                <div class="cc-why-matches">
                    <div class="cc-why-title">Why it matches you</div>
                    <div class="cc-why-text">
                        Your experience as {current_role} and skills in {matched}
                        align with the requirements of this role.
                    </div>
                </div>
                """
            )

        # Footer row
        footer_left, footer_right = st.columns([2, 2], vertical_alignment="center")

        with footer_left:
            st.caption(employment_label)

        with footer_right:
            btn_save, btn_view = st.columns(2)

            with btn_save:
                st.button(
                    "Save",
                    key=f"job_save_{i}",
                    use_container_width=True
                )

            with btn_view:
                if job_url:
                    st.link_button(
                        "View details ↗",
                        url=str(job_url),
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.button(
                        "View details ↗",
                        key=f"job_view_{i}",
                        type="primary",
                        use_container_width=True,
                        disabled=True
                    )


# --- If no structured jobs but analysis exists, show analysis ---
if not jobs and analysis:
    st.subheader("Agent Recommendations")
    st.markdown(analysis)
