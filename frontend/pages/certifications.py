from pathlib import Path
from html import escape

import requests
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Certifications | CareerCompass",
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
# PAGE-SPECIFIC STYLES
# =========================================================

st.html(
    """
    <style>

    .cert-page {
        padding-top: 12px;
    }

    .cert-eyebrow {
        color: #1597E5;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 14px;
    }

    .cert-title {
        color: #0B2E4F;
        font-size: 46px;
        line-height: 1.1;
        font-weight: 700;
        margin: 0;
    }

    .cert-subtitle {
        color: #627D98;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 34px;
    }

    .cert-name {
        color: #0B2E4F;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .cert-meta {
        color: #627D98;
        font-size: 14px;
        margin-bottom: 12px;
    }

    .cert-section-label {
        color: #627D98;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 7px;
    }

    .cert-reason {
        color: #627D98;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 15px;
    }

    .skill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        align-items: center;
    }

    .skill-pill-match {
        background: #E6F7F2;
        color: #16705A;
        border-radius: 8px;
        padding: 5px 10px;
        font-size: 11px;
    }

    .skill-pill-missing {
        background: #FDEDEE;
        color: #94515A;
        border-radius: 8px;
        padding: 5px 10px;
        font-size: 11px;
    }

    .priority-high {
        display: inline-block;
        padding: 6px 13px;
        border-radius: 999px;
        background: #E6F5FD;
        color: #1597E5;
        border: 1px solid #A8DDF8;
        font-size: 12px;
        font-weight: 600;
    }

    .priority-medium {
        display: inline-block;
        padding: 6px 13px;
        border-radius: 999px;
        background: #EEF3F7;
        color: #627D98;
        border: 1px solid #D9E2EC;
        font-size: 12px;
        font-weight: 600;
    }

    .priority-low {
        display: inline-block;
        padding: 6px 13px;
        border-radius: 999px;
        background: #F5F7FA;
        color: #829AB1;
        border: 1px solid #D9E2EC;
        font-size: 12px;
        font-weight: 600;
    }

    </style>
    """
)


# =========================================================
# AUTH GUARD
# =========================================================

token = st.session_state.get("token")

if not token:

    st.warning(
        "Please sign in to view your certification recommendations."
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
# NAVBAR
# =========================================================

with st.container(
    key="certs_nav",
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

            <a href="#">
                Dashboard
            </a>

            <a href="#">
                Jobs
            </a>

            <a href="#">
                Freelance
            </a>

            <a class="active" href="#">
                Certifications
            </a>

            <a href="#">
                Profile
            </a>

        </nav>
        """
    )

    if st.button(
        "← Dashboard",
        key="certs_nav_back",
        type="tertiary",
    ):
        st.switch_page(
            "pages/dashboard.py"
        )


st.divider()


# =========================================================
# HEADER
# =========================================================

with st.container(
    key="certifications_header",
):

    st.html(
        """
        <div class="cert-page">

            <div class="cert-eyebrow">
                MAKE YOUR NEXT QUALIFICATION COUNT
            </div>

            <h1 class="cert-title">
                Recommended certifications for you.
            </h1>

            <p class="cert-subtitle">
                Based on your skills, education, and experience.
            </p>

        </div>
        """
    )


# =========================================================
# LOAD RECOMMENDATIONS
# =========================================================

if "cert_recommendations" not in st.session_state:

    with st.spinner(
        "Finding certifications matched to your profile..."
    ):

        try:

            response = requests.post(
                f"{API_BASE}/api/career/certifications",
                headers={
                    "Authorization":
                        f"Bearer {token}"
                },
                timeout=180,
            )

            if response.status_code == 200:

                data = response.json()

                st.session_state[
                    "cert_recommendations"
                ] = data.get(
                    "recommendations",
                    [],
                )

                st.session_state[
                    "cert_rec_analysis"
                ] = data.get(
                    "analysis",
                    "",
                )

            else:

                st.session_state[
                    "cert_recommendations"
                ] = []

                st.error(
                     f"Backend error {response.status_code}: "
                    f"{response.text}"
                )

        except requests.Timeout:

            st.session_state[
                "cert_recommendations"
            ] = []

            st.error(
                "Certification recommendations "
                "took too long to load."
            )

        except requests.RequestException as error:

            st.session_state[
                "cert_recommendations"
            ] = []

            st.error(
                f"Could not reach the API: {error}"
            )


recommendations = st.session_state.get(
    "cert_recommendations",
    [],
)


# =========================================================
# VISIBLE RECOMMENDATION COUNT
# =========================================================

if "cert_visible_count" not in st.session_state:

    st.session_state["cert_visible_count"] = 5


visible_count = st.session_state[
    "cert_visible_count"
]


# =========================================================
# HELPERS
# =========================================================

def render_skill_pills(
    skills: list[str],
    css_class: str,
) -> str:

    if not skills:
        return (
            '<span style="color:#9FB3C8; '
            'font-size:12px;">'
            "None listed"
            "</span>"
        )

    return "".join(
        f'<span class="{css_class}">'
        f'{escape(str(skill))}'
        "</span>"
        for skill in skills
    )


def priority_class(
    priority: str,
) -> str:

    priority = priority.lower()

    if priority == "high":
        return "priority-high"

    if priority == "low":
        return "priority-low"

    return "priority-medium"


# =========================================================
# EMPTY STATE
# =========================================================

if not recommendations:

    with st.container(
        border=True,
        key="cert_empty_state",
    ):

        with st.container(
            horizontal_alignment="center",
        ):

            st.markdown(
                ":material/workspace_premium:"
            )

            st.subheader(
                "No certification recommendations yet",
                anchor=False,
            )

            st.caption(
                "Complete your profile so CareerCompass "
                "can identify certifications that match "
                "your background."
            )


# =========================================================
# RECOMMENDATION CARDS
# =========================================================

else:

    shown_recommendations = recommendations[
        :visible_count
    ]

    for index, recommendation in enumerate(
        shown_recommendations
    ):

        exam_name = recommendation.get(
            "name",
            "Certification",
        )

        provider = recommendation.get(
            "provider",
            "",
        )

        exam_code = recommendation.get(
            "exam_code",
        )

        priority = str(
            recommendation.get(
                "priority",
                "medium",
            )
        ).lower()

        match = recommendation.get(
            "match",
            {},
        ) or {}

        explanation = match.get(
            "explanation",
            "",
        )

        matching_skills = match.get(
            "matching_skills",
            [],
        ) or []

        missing_skills = match.get(
            "missing_skills",
            [],
        ) or []

        score = match.get(
            "score",
        )

        # -----------------------------------------
        # Card
        # -----------------------------------------

        with st.container(
            border=True,
            key=f"cert_card_{index}",
        ):

            main_col, action_col = st.columns(
                [5, 1.25],
                gap="large",
                vertical_alignment="center",
            )

            # -------------------------------------
            # LEFT SIDE
            # -------------------------------------

            with main_col:

                safe_name = escape(
                    str(exam_name)
                )

                safe_provider = escape(
                    str(provider)
                )

                safe_code = escape(
                    str(exam_code)
                ) if exam_code else "Not available"

                safe_explanation = escape(
                    str(explanation)
                )

                st.html(
                    f"""
                    <div class="cert-name">
                        {safe_name}
                    </div>

                    <div class="cert-meta">
                        {safe_provider}
                        &nbsp; | &nbsp;
                        Exam code: {safe_code}
                    </div>

                    <div class="cert-section-label">
                        Why it fits you
                    </div>

                    <div class="cert-reason">
                        {safe_explanation}
                    </div>
                    """
                )

                skills_left, skills_right = st.columns(
                    2,
                    gap="large",
                )

                with skills_left:

                    matching_html = (
                        render_skill_pills(
                            matching_skills,
                            "skill-pill-match",
                        )
                    )

                    st.html(
                        f"""
                        <div class="cert-section-label">
                            Matching skills
                        </div>

                        <div class="skill-row">
                            {matching_html}
                        </div>
                        """
                    )

                with skills_right:

                    missing_html = (
                        render_skill_pills(
                            missing_skills,
                            "skill-pill-missing",
                        )
                    )

                    st.html(
                        f"""
                        <div class="cert-section-label">
                            Missing skills
                        </div>

                        <div class="skill-row">
                            {missing_html}
                        </div>
                        """
                    )

            # -------------------------------------
            # RIGHT SIDE
            # -------------------------------------

            with action_col:

                badge_class = priority_class(
                    priority
                )

                priority_label = (
                    priority.title()
                )

                score_text = ""

                if score is not None:
                    score_text = (
                        f"<div style='"
                        "color:#627D98;"
                        "font-size:11px;"
                        "margin-top:6px;'>"
                        f"Match score: {score}%"
                        "</div>"
                    )

                st.html(
                    f"""
                    <div style="
                        text-align:center;
                        margin-bottom:18px;
                    ">
                        <span class="{badge_class}">
                            {priority_label} Priority
                        </span>

                        {score_text}
                    </div>
                    """
                )

                if st.button(
                    "View certification →",
                    key=f"view_certification_{index}",
                    type="primary",
                    use_container_width=True,
                ):

                    # Store the full recommendation.
                    # In the next step the details page
                    # will read this object.

                    st.session_state[
                        "selected_certification"
                    ] = recommendation

                    st.switch_page(
                        "pages/certification_details.py"
                    )


# =========================================================
# SHOW MORE
# =========================================================

if (
    recommendations
    and visible_count < len(recommendations)
):

    remaining = len(recommendations) - visible_count

    center_left, center, center_right = st.columns(
        [2, 1.4, 2]
    )

    with center:

        if st.button(
            f"Show more certifications ({remaining})",
            key="show_more_certifications",
            type="secondary",
            use_container_width=True,
        ):

            st.session_state["cert_visible_count"] += 5

            st.rerun()


# =========================================================
# SHOW MORE
# =========================================================

if (
    recommendations
    and visible_count < len(recommendations)
):

    remaining = len(recommendations) - visible_count

    center_left, center, center_right = st.columns(
        [2, 1.4, 2]
    )

    with center:

        if st.button(
            f"Show more certifications ({remaining})",
            key="show_more_certifications",
            type="secondary",
            use_container_width=True,
        ):

            st.session_state["cert_visible_count"] += 5
            st.rerun()

