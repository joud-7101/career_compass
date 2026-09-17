from pathlib import Path
import streamlit as st
import requests

# ---------------------------------
# Page settings
# ---------------------------------

st.set_page_config(
    page_title="Certifications | CareerCompass",
    page_icon=":material/workspace_premium:",
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
    st.warning("Please sign in to view your certification recommendations.")
    if st.button("Sign in", type="primary"):
        st.switch_page("pages/sign_in.py")
    st.stop()


# =================================
# NAVBAR
# =================================

with st.container(
    key="certs_nav",
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
            <a href="#">Freelance</a>
            <a class="active" href="#">Certifications</a>
            <a href="#">Profile</a>
        </nav>
        """
    )

    if st.button("← Dashboard", key="certs_nav_back", type="tertiary"):
        st.switch_page("pages/dashboard.py")


# =================================
# HEADER
# =================================

with st.container(key="certs_hero"):

    left, right = st.columns([2, 1], vertical_alignment="center")

    with left:
        st.html('<p class="cc-dashboard-eyebrow">MAKE YOUR NEXT QUALIFICATION COUNT</p>')
        st.html('<h1 class="cc-dashboard-title">Certification study planner.</h1>')
        st.html(
            '<p class="cc-dashboard-subtitle">'
            "Create a study plan based on your certification, "
            "current level, and exam date."
            "</p>"
        )

    with right:
        with st.container(horizontal_alignment="right"):
            st.button(
                "Sample profile & recommendations",
                key="certs_sample_btn",
                type="secondary"
            )


# =================================
# STAGE 1: LOAD RECOMMENDATIONS
# =================================

if "cert_recommendations" not in st.session_state:
    with st.spinner("Finding certifications matched to your profile..."):
        try:
            resp = requests.post(
                f"{API_BASE}/api/career/certifications",
                headers={"Authorization": f"Bearer {token}"},
                timeout=120,
            )

            if resp.status_code == 200:
                data = resp.json()
                st.session_state["cert_recommendations"] = data.get("recommendations", [])
                st.session_state["cert_rec_analysis"] = data.get("analysis", "")
            else:
                st.session_state["cert_recommendations"] = []
                st.session_state["cert_rec_analysis"] = ""

        except requests.Timeout:
            st.session_state["cert_recommendations"] = []
            st.session_state["cert_rec_analysis"] = ""
            st.warning("Recommendation load timed out. You can still enter a certification manually.")

        except requests.RequestException as e:
            st.session_state["cert_recommendations"] = []
            st.session_state["cert_rec_analysis"] = ""
            st.warning(f"Could not reach the API: {e}")


recommendations = st.session_state.get("cert_recommendations", [])


# =================================
# STAGE 2 FORM — Study plan inputs
# =================================

with st.container(key="certs_form_card", border=True):

    # Pre-fill cert name if user clicked a recommendation card
    prefill_cert = st.session_state.get("selected_cert_name", "")

    form_col1, form_col2, form_col3, form_col4 = st.columns(
        [2.5, 1.5, 1.5, 1.5],
        gap="medium",
        vertical_alignment="bottom"
    )

    with form_col1:
        cert_name = st.text_input(
            "Certification name",
            value=prefill_cert,
            placeholder="e.g. Microsoft Power BI Data Analyst (PL-300)",
            key="cert_name_input"
        )

    with form_col2:
        current_level = st.selectbox(
            "Current level",
            options=["Beginner", "Intermediate", "Advanced"],
            index=1,
            key="cert_level_select"
        )

    with form_col3:
        exam_date = st.date_input(
            "Exam date",
            value=None,
            key="cert_date_input"
        )

    with form_col4:
        create_plan = st.button(
            "Create study plan →",
            type="primary",
            use_container_width=True,
            key="cert_create_plan_btn"
        )


# =================================
# STAGE 2: GENERATE STUDY PLAN
# =================================

if create_plan:
    if not cert_name:
        st.warning("Please enter a certification name.")
    elif not exam_date:
        st.warning("Please select an exam date.")
    else:
        st.session_state.pop("study_plan_result", None)

        with st.spinner(f"Creating your personalised study plan for **{cert_name}**..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/career/certifications/study-plan",
                    json={
                        "selected_certification": cert_name,
                        "current_level": current_level,
                        "exam_date": str(exam_date),
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=120,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["study_plan_result"] = data.get("study_plan", "")
                    st.session_state["study_plan_cert"] = cert_name
                else:
                    st.error(
                        f"Could not generate study plan "
                        f"(status {resp.status_code}): {resp.text[:300]}"
                    )

            except requests.Timeout:
                st.error(
                    "The certification agent took too long. "
                    "Please try again."
                )

            except requests.RequestException as e:
                st.error(f"Could not reach the API: {e}")


# =================================
# STUDY PLAN OUTPUT
# =================================

study_plan = st.session_state.get("study_plan_result")

if study_plan:
    with st.container(key="certs_plan_card", border=True):
        st.subheader(
            f":material/menu_book: Study Plan — "
            f"{st.session_state.get('study_plan_cert', cert_name)}"
        )
        st.divider()
        st.markdown(study_plan)

        refresh_plan = st.button(
            ":material/refresh: Regenerate plan",
            key="cert_regen_btn",
            type="tertiary"
        )
        if refresh_plan:
            st.session_state.pop("study_plan_result", None)
            st.rerun()

else:
    # Placeholder when no plan generated yet
    with st.container(key="certs_placeholder", border=True):
        with st.container(horizontal_alignment="center"):
            st.markdown(":material/menu_book:")
            st.subheader(
                "Your next goal, broken into clear steps.",
                anchor=False
            )
            st.caption(
                "Choose a certification and exam date to see your study "
                "priorities and a week-by-week plan."
            )


# =================================
# RECOMMENDATION CARDS
# =================================

if recommendations:
    st.divider()

    st.markdown("#### Recommended for your profile")
    st.caption(
        "Based on your skills and experience — click any certification "
        "to auto-fill the form above."
    )

    # Priority colour map
    priority_colours = {
        "High": "#1597E5",
        "Medium": "#627D98",
        "Low": "#9FB3C8",
    }

    for rec in recommendations:
        exam_name = rec.get("exam_name", "")
        exam_code = rec.get("exam_code", "")
        certifying_body = rec.get("certifying_body", "")
        reason = rec.get("reason", "")
        priority = rec.get("priority", "Medium")
        colour = priority_colours.get(priority, "#627D98")

        display_label = exam_name
        if exam_code:
            display_label += f" ({exam_code})"

        with st.container(key=f"cert_rec_{exam_name[:20]}", border=True):

            left_rec, right_rec = st.columns([4, 1], vertical_alignment="center")

            with left_rec:
                st.html(
                    f"""
                    <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                        <div>
                            <div class="cc-profile-value" style="font-size:16px; margin:0;">
                                {display_label}
                            </div>
                            <div class="cc-profile-detail" style="margin:2px 0 6px;">
                                {certifying_body}
                            </div>
                            <div style="font-size:13px; color:#627D98;">
                                {reason}
                            </div>
                        </div>
                    </div>
                    """
                )

            with right_rec:
                # Priority badge + select button
                st.html(
                    f'<span class="cc-priority-badge" '
                    f'style="background:{colour}20; color:{colour}; '
                    f'border:1px solid {colour}40;">'
                    f'{priority} Priority</span>'
                )

                if st.button(
                    "Select",
                    key=f"cert_select_{exam_name[:20]}",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state["selected_cert_name"] = exam_name
                    st.rerun()

    # Refresh recs
    if st.button(
        ":material/refresh: Refresh recommendations",
        key="certs_refresh",
        type="tertiary"
    ):
        for k in ["cert_recommendations", "cert_rec_analysis"]:
            st.session_state.pop(k, None)
        st.rerun()
