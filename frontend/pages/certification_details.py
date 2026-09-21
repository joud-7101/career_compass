from pathlib import Path
from html import escape

import requests
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Certification Details | CareerCompass",
    page_icon=":material/workspace_premium:",
    layout="wide",
)


# =========================================================
# FILES / API
# =========================================================

ASSETS = Path(__file__).resolve().parents[1] / "assets"

st.html(ASSETS / "home.css")

logo = ASSETS / "logo.png"

API_BASE = "http://127.0.0.1:8000"


# =========================================================
# PAGE CSS
# =========================================================

st.html(
    """
    <style>

    /* -----------------------------
       PAGE
    ----------------------------- */

    .cc-cert-title {
        color: #0B2E4F;
        font-size: 38px;
        font-weight: 700;
        line-height: 1.15;
        margin: 0 0 8px 0;
    }

    .cc-cert-meta {
        color: #627D98;
        font-size: 16px;
        margin-bottom: 14px;
    }

    .cc-cert-description {
        color: #627D98;
        font-size: 16px;
        line-height: 1.6;
        max-width: 720px;
    }


    /* -----------------------------
       SECTION HEADER
    ----------------------------- */

    .cc-section-header {
        display: flex;
        gap: 15px;
        align-items: flex-start;
        margin-bottom: 22px;
    }

    .cc-section-number {
        min-width: 48px;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #E8F5FD;
        color: #1597E5;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 18px;
        font-weight: 700;
    }

    .cc-section-title {
        color: #0B2E4F;
        font-size: 21px;
        font-weight: 700;
        margin: 0;
    }

    .cc-section-subtitle {
        color: #829AB1;
        font-size: 13px;
        margin-top: 3px;
    }


    /* -----------------------------
       EXAM INFO
    ----------------------------- */

    .cc-info-row {
        display: grid;
        grid-template-columns: 155px 1fr;
        gap: 14px;
        margin-bottom: 15px;
    }

    .cc-info-label {
        color: #627D98;
        font-size: 13px;
    }

    .cc-info-value {
        color: #102A43;
        font-size: 13px;
        font-weight: 500;
    }


    /* -----------------------------
       DOMAINS
    ----------------------------- */

    .cc-domain-title {
        color: #102A43;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .cc-domain-subtitle {
        color: #829AB1;
        font-size: 12px;
        margin-bottom: 14px;
    }

    .cc-domain-row {
        display: grid;
        grid-template-columns: 34px 1fr auto;
        align-items: center;
        gap: 10px;

        padding: 10px 0;
        border-bottom: 1px solid #E6EEF5;
    }

    .cc-domain-number {
        width: 27px;
        height: 27px;
        border-radius: 50%;

        background: #E8F5FD;
        color: #1597E5;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 12px;
        font-weight: 700;
    }

    .cc-domain-name {
        color: #102A43;
        font-size: 13px;
    }

    .cc-domain-weight {
        color: #102A43;
        font-size: 13px;
        font-weight: 500;
    }


    /* -----------------------------
       STUDY PLAN SUB-CARDS
    ----------------------------- */

    .cc-plan-heading {
        color: #102A43;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .cc-plan-caption {
        color: #829AB1;
        font-size: 11px;
        margin-bottom: 12px;
    }

    .cc-plan-box {
        background: #F7F9FC;
        border-radius: 9px;
        padding: 15px;
        min-height: 165px;
    }

    .cc-placeholder-text {
        color: #829AB1;
        font-size: 13px;
        line-height: 1.7;
    }


    /* -----------------------------
       RESOURCE ROW
    ----------------------------- */

    .cc-resource-row {
        border: 1px solid #D9E2EC;
        border-radius: 9px;
        padding: 11px 14px;
        margin-bottom: 7px;

        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .cc-resource-name {
        color: #102A43;
        font-size: 13px;
        font-weight: 600;
    }

    .cc-resource-provider {
        color: #829AB1;
        font-size: 11px;
        margin-top: 2px;
    }

    .cc-resource-open {
        color: #1597E5;
        font-size: 12px;
        font-weight: 600;
    }


    /* -----------------------------
       NOTES
    ----------------------------- */

    .cc-notes-box {
        background: #EAF6FD;
        border-radius: 9px;
        padding: 15px;
        color: #627D98;
        font-size: 12px;
        line-height: 1.6;
    }

    </style>
    """
)


# =========================================================
# AUTH
# =========================================================

token = st.session_state.get("token")

if not token:

    st.warning(
        "Please sign in to view certification details."
    )

    if st.button(
        "Sign in",
        type="primary",
    ):
        st.switch_page(
            "pages/sign_in.py"
        )

    st.stop()


# =========================================================
# SELECTED CERTIFICATION
# =========================================================

selected = st.session_state.get(
    "selected_certification"
)

if not selected:

    st.warning(
        "No certification was selected."
    )

    if st.button(
        "← Back to Certifications",
        type="secondary",
    ):
        st.switch_page(
            "pages/certifications.py"
        )

    st.stop()


exam_id = selected.get("exam_id")

exam_name = selected.get(
    "name",
    "Certification"
)

exam_code = selected.get(
    "exam_code"
)

provider = selected.get(
    "provider",
    ""
)

match = selected.get(
    "match",
    {}
) or {}

description = match.get(
    "explanation",
    ""
)


# =========================================================
# NAVBAR
# =========================================================

with st.container(
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
):

    st.image(
        logo,
        width=170,
    )

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

    st.write("")


st.divider()


# =========================================================
# BACK BUTTON
# =========================================================

if st.button(
    "← Back to Certifications",
    type="tertiary",
    key="back_to_certifications",
):
    st.switch_page(
        "pages/certifications.py"
    )


# =========================================================
# HERO + FORM
# =========================================================

hero_left, hero_right = st.columns(
    [1.45, 1],
    gap="large",
    vertical_alignment="center",
)


# LEFT — certification
with hero_left:

    safe_name = escape(
        str(exam_name)
    )

    safe_code = escape(
        str(
            exam_code
            or "Exam code unavailable"
        )
    )

    safe_provider = escape(
        str(provider)
    )

    safe_description = escape(
        str(description)
    )

    st.html(
        f"""
        <h1 class="cc-cert-title">
            {safe_name}
        </h1>

        <div class="cc-cert-meta">
            {safe_code}
            &nbsp; • &nbsp;
            {safe_provider}
        </div>

        <div class="cc-cert-description">
            {safe_description}
        </div>
        """
    )


# RIGHT — plan setup
with hero_right:

    with st.container(
        border=True,
        key="study_plan_setup",
    ):

        st.markdown(
            "### Prepare your study plan"
        )

        st.caption(
            "Set your current level and target exam date "
            "to generate a personalized plan."
        )

        level_col, date_col = st.columns(
            2,
            gap="medium",
        )

        with level_col:

            current_level = st.selectbox(
                "Current level",
                [
                    "Beginner",
                    "Intermediate",
                    "Advanced",
                ],
                key="cert_current_level",
            )

        with date_col:

            exam_date = st.date_input(
                "Exam date",
                value=None,
                key="cert_exam_date",
            )

        create_plan = st.button(
            "Create study plan →",
            type="primary",
            use_container_width=True,
            key="create_cert_plan",
        )


# =========================================================
# CREATE STUDY PLAN
# =========================================================

if create_plan:

    if not exam_date:

        st.warning(
            "Please select an exam date."
        )

    else:

        selected_identifier = (
            exam_id
            or exam_name
        )

        with st.spinner(
            "Creating your personalized study plan..."
        ):

            try:

                response = requests.post(
                    f"{API_BASE}/api/career/"
                    "certifications/study-plan",
                    json={
                        "selected_certification":
                            selected_identifier,
                        "current_level":
                            current_level,
                        "exam_date":
                            str(exam_date),
                    },
                    headers={
                        "Authorization":
                            f"Bearer {token}"
                    },
                    timeout=180,
                )

                if response.status_code == 200:

                    st.session_state[
                        "cert_plan_response"
                    ] = response.json()

                    st.session_state[
                        "cert_plan_created"
                    ] = True

                else:

                    st.error(
                        f"Could not generate plan "
                        f"({response.status_code})."
                    )

            except requests.RequestException as error:

                st.error(
                    f"Could not reach API: {error}"
                )


# =========================================================
# RESULT PLACEHOLDERS
# =========================================================

plan_created = st.session_state.get(
    "cert_plan_created",
    False
)


st.write("")
st.write("")


# =========================================================
# TWO COLUMN RESULTS
# =========================================================

main_col, side_col = st.columns(
    [2.05, 1],
    gap="large",
)


# =========================================================
# LEFT COLUMN
# =========================================================

with main_col:

    # -----------------------------------------------------
    # 01 EXAM INFORMATION
    # -----------------------------------------------------

    with st.container(
        border=True,
        key="exam_information_card",
    ):

        st.html(
            """
            <div class="cc-section-header">

                <div class="cc-section-number">
                    01
                </div>

                <div>
                    <div class="cc-section-title">
                        Exam Information
                    </div>

                    <div class="cc-section-subtitle">
                        Key details about this certification and exam.
                    </div>
                </div>

            </div>
            """
        )

        info_col, domain_col = st.columns(
            [1, 1.15],
            gap="large",
        )

        # ---------------------------------------------
        # Exam information
        # ---------------------------------------------

        with info_col:

            exam_rows = [
                (
                    "Certification Name",
                    exam_name,
                ),
                (
                    "Exam Code",
                    exam_code or "—",
                ),
                (
                    "Certifying Body",
                    provider or "—",
                ),
                (
                    "Number of Questions",
                    "—",
                ),
                (
                    "Exam Duration",
                    "—",
                ),
                (
                    "Exam Format",
                    "—",
                ),
                (
                    "Official Practice Exam",
                    "—",
                ),
            ]

            for label, value in exam_rows:

                st.html(
                    f"""
                    <div class="cc-info-row">

                        <div class="cc-info-label">
                            {escape(str(label))}
                        </div>

                        <div class="cc-info-value">
                            {escape(str(value))}
                        </div>

                    </div>
                    """
                )

        # ---------------------------------------------
        # Domains
        # ---------------------------------------------

        with domain_col:

            st.html(
                """
                <div class="cc-domain-title">
                    Exam Domains
                </div>

                <div class="cc-domain-subtitle">
                    The exam covers the following
                    domains and weightings.
                </div>
                """
            )

            # Backend structured data comes later.
            # For now keep the correct UI shape.

            for i in range(1, 5):

                st.html(
                    f"""
                    <div class="cc-domain-row">

                        <div class="cc-domain-number">
                            {i}
                        </div>

                        <div class="cc-domain-name">
                            Domain information
                        </div>

                        <div class="cc-domain-weight">
                            —
                        </div>

                    </div>
                    """
                )


    st.write("")


    # -----------------------------------------------------
    # 02 PERSONALIZED STUDY PLAN
    # -----------------------------------------------------

    with st.container(
        border=True,
        key="personalized_plan_card",
    ):

        st.html(
            """
            <div class="cc-section-header">

                <div class="cc-section-number">
                    02
                </div>

                <div>
                    <div class="cc-section-title">
                        Personalized Study Plan
                    </div>

                    <div class="cc-section-subtitle">
                        A tailored plan based on your
                        level and exam date.
                    </div>
                </div>

            </div>
            """
        )

        priority_col, week_col, prep_col = st.columns(
            3,
            gap="medium",
        )


        # ---------------------------------------------
        # Study priorities
        # ---------------------------------------------

        with priority_col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    "#### 🎯 Study Priorities"
                )

                st.caption(
                    "Focus on the most important areas."
                )

                st.html(
                    """
                    <div class="cc-plan-box">

                        <div class="cc-placeholder-text">
                            Your personalized study
                            priorities will appear here
                            after the study plan is generated.
                        </div>

                    </div>
                    """
                )


        # ---------------------------------------------
        # Weekly plan
        # ---------------------------------------------

        with week_col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    "#### 📅 Weekly Plan"
                )

                st.caption(
                    "Your week-by-week preparation."
                )

                st.html(
                    """
                    <div class="cc-plan-box">

                        <div class="cc-placeholder-text">
                            Week 1<br><br>
                            Week 2<br><br>
                            Week 3<br><br>
                            Final review
                        </div>

                    </div>
                    """
                )


        # ---------------------------------------------
        # Exam preparation
        # ---------------------------------------------

        with prep_col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    "#### 🎓 Exam Preparation"
                )

                st.caption(
                    "Activities to build exam readiness."
                )

                st.html(
                    """
                    <div class="cc-plan-box">

                        <div class="cc-placeholder-text">
                            Your practice strategy,
                            final revision and exam
                            preparation will appear here.
                        </div>

                    </div>
                    """
                )


# =========================================================
# RIGHT COLUMN
# =========================================================

with side_col:

    # -----------------------------------------------------
    # 03 RESOURCES
    # -----------------------------------------------------

    with st.container(
        border=True,
        key="resources_card",
    ):

        st.html(
            """
            <div class="cc-section-header">

                <div class="cc-section-number">
                    03
                </div>

                <div>
                    <div class="cc-section-title">
                        Practice & Official Resources
                    </div>

                    <div class="cc-section-subtitle">
                        Official resources for your exam.
                    </div>
                </div>

            </div>
            """
        )

        resources = [
            "Official exam page",
            "Official practice assessment",
            "Official study guide",
            "Official learning resources",
        ]

        for resource in resources:

            st.html(
                f"""
                <div class="cc-resource-row">

                    <div>
                        <div class="cc-resource-name">
                            {resource}
                        </div>

                        <div class="cc-resource-provider">
                            Available after plan generation
                        </div>
                    </div>

                    <div class="cc-resource-open">
                        Open →
                    </div>

                </div>
                """
            )


    st.write("")


    # -----------------------------------------------------
    # IMPORTANT NOTES
    # -----------------------------------------------------

    with st.container(
        border=True,
        key="important_notes_card",
    ):

        st.html(
            """
            <div class="cc-section-header">

                <div class="cc-section-number">
                    i
                </div>

                <div>
                    <div class="cc-section-title">
                        Important Notes
                    </div>

                    <div class="cc-section-subtitle">
                        Keep these in mind as you prepare.
                    </div>
                </div>

            </div>
            """
        )

        st.html(
            """
            <div class="cc-notes-box">

                Important exam notes, retake policy,
                missing information and source updates
                will appear here after the plan is generated.

            </div>
            """
        )