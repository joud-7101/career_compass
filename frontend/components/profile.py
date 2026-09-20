import sys
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.schemas.profile import UserProfile

def render_profile_editor(profile_data: dict) -> UserProfile | None:
    """
    Render an editable Profile Review form and return
    a validated UserProfile when the user saves it.
    """

    try:
        profile = UserProfile.model_validate(profile_data)
    except ValidationError as e:
        st.error("Could not load the extracted profile.")
        st.code(str(e))
        return None

    st.subheader("Profile Review")
    st.caption(
        "Review the information extracted from your CV and portfolio "
        "and make any changes before continuing."
    )

    # --------------------------------------------------
    # Personal Information
    # --------------------------------------------------
    st.markdown("### Personal Information")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Name",
            value=profile.personal_information.name or "",
        )

        email = st.text_input(
            "Email",
            value=profile.personal_information.email or "",
        )

    with col2:
        phone = st.text_input(
            "Phone",
            value=profile.personal_information.phone or "",
        )

        location = st.text_input(
            "Location",
            value=profile.personal_information.location or "",
        )

    # --------------------------------------------------
    # Professional Summary
    # --------------------------------------------------
    st.markdown("### Professional Summary")

    professional_summary = st.text_area(
        "Summary",
        value=profile.professional_summary or "",
        height=130,
    )

    # --------------------------------------------------
    # Skills
    # --------------------------------------------------
    st.markdown("### Skills")

    skills_text = st.text_area(
        "Skills",
        value=", ".join(skill.name for skill in profile.skills),
        help="Separate skills with commas.",
        height=100,
    )

    # --------------------------------------------------
    # Education
    # --------------------------------------------------
    st.markdown("### Education")

    education = []

    for i, item in enumerate(profile.education):
        with st.expander(
            f"Education {i + 1}: {item.institution}",
            expanded=True,
        ):
            institution = st.text_input(
                "Institution",
                value=item.institution,
                key=f"education_institution_{i}",
            )

            degree = st.text_input(
                "Degree",
                value=item.degree or "",
                key=f"education_degree_{i}",
            )

            field = st.text_input(
                "Field of Study",
                value=item.field_of_study or "",
                key=f"education_field_{i}",
            )

            start_date = st.text_input(
                "Start Date",
                value=item.start_date or "",
                key=f"education_start_{i}",
            )

            end_date = st.text_input(
                "End Date",
                value=item.end_date or "",
                key=f"education_end_{i}",
            )

            education.append(
                {
                    "institution": institution,
                    "degree": degree or None,
                    "field_of_study": field or None,
                    "start_date": start_date or None,
                    "end_date": end_date or None,
                    "source": item.source,
                }
            )

    # --------------------------------------------------
    # Experience
    # --------------------------------------------------
    st.markdown("### Experience")

    experience = []

    for i, item in enumerate(profile.experience):
        with st.expander(
            f"Experience {i + 1}: {item.title}",
            expanded=True,
        ):
            title = st.text_input(
                "Job Title",
                value=item.title,
                key=f"experience_title_{i}",
            )

            company = st.text_input(
                "Company",
                value=item.company or "",
                key=f"experience_company_{i}",
            )

            location_exp = st.text_input(
                "Location",
                value=item.location or "",
                key=f"experience_location_{i}",
            )

            start_date = st.text_input(
                "Start Date",
                value=item.start_date or "",
                key=f"experience_start_{i}",
            )

            end_date = st.text_input(
                "End Date",
                value=item.end_date or "",
                key=f"experience_end_{i}",
            )

            description = st.text_area(
                "Description",
                value=item.description or "",
                key=f"experience_description_{i}",
            )

            skills = st.text_input(
                "Skills Used",
                value=", ".join(item.skills),
                key=f"experience_skills_{i}",
            )

            experience.append(
                {
                    "title": title,
                    "company": company or None,
                    "location": location_exp or None,
                    "start_date": start_date or None,
                    "end_date": end_date or None,
                    "description": description or None,
                    "skills": [
                        s.strip()
                        for s in skills.split(",")
                        if s.strip()
                    ],
                    "source": item.source,
                }
            )

    # --------------------------------------------------
    # Projects
    # --------------------------------------------------
    st.markdown("### Projects")

    projects = []

    for i, item in enumerate(profile.projects):
        with st.expander(
            f"Project {i + 1}: {item.name}",
            expanded=True,
        ):
            project_name = st.text_input(
                "Project Name",
                value=item.name,
                key=f"project_name_{i}",
            )

            description = st.text_area(
                "Description",
                value=item.description or "",
                key=f"project_description_{i}",
            )

            technologies = st.text_input(
                "Technologies",
                value=", ".join(item.technologies),
                key=f"project_technologies_{i}",
            )

            url = st.text_input(
                "Project URL",
                value=str(item.url) if item.url else "",
                key=f"project_url_{i}",
            )

            repository_url = st.text_input(
                "Repository URL",
                value=str(item.repository_url)
                if item.repository_url
                else "",
                key=f"project_repository_{i}",
            )

            projects.append(
                {
                    "name": project_name,
                    "description": description or None,
                    "technologies": [
                        tech.strip()
                        for tech in technologies.split(",")
                        if tech.strip()
                    ],
                    "url": url or None,
                    "repository_url": repository_url or None,
                    "source": item.source,
                }
            )

    # --------------------------------------------------
    # Certifications
    # --------------------------------------------------
    st.markdown("### Certifications")

    certifications = []

    for i, item in enumerate(profile.certifications):
        with st.expander(
            f"Certification {i + 1}: {item.name}",
            expanded=False,
        ):
            cert_name = st.text_input(
                "Certification Name",
                value=item.name,
                key=f"cert_name_{i}",
            )

            issuer = st.text_input(
                "Issuer",
                value=item.issuer or "",
                key=f"cert_issuer_{i}",
            )

            credential_id = st.text_input(
                "Credential ID",
                value=item.credential_id or "",
                key=f"cert_id_{i}",
            )

            credential_url = st.text_input(
                "Credential URL",
                value=str(item.credential_url)
                if item.credential_url
                else "",
                key=f"cert_url_{i}",
            )

            issue_date = st.text_input(
                "Issue Date",
                value=item.issue_date or "",
                key=f"cert_issue_{i}",
            )

            expiry_date = st.text_input(
                "Expiry Date",
                value=item.expiry_date or "",
                key=f"cert_expiry_{i}",
            )

            certifications.append(
                {
                    "name": cert_name,
                    "issuer": issuer or None,
                    "credential_id": credential_id or None,
                    "credential_url": credential_url or None,
                    "issue_date": issue_date or None,
                    "expiry_date": expiry_date or None,
                    "source": item.source,
                }
            )

    # --------------------------------------------------
    # Languages
    # --------------------------------------------------
    st.markdown("### Languages")

    languages_text = st.text_input(
        "Languages",
        value=", ".join(profile.languages),
    )

    # --------------------------------------------------
    # Professional Links
    # --------------------------------------------------
    st.markdown("### Professional Links")

    professional_links = []

    for i, item in enumerate(profile.professional_links):
        with st.expander(
            f"Link {i + 1}: {item.label or item.kind}",
            expanded=False,
        ):
            link_url = st.text_input(
                "URL",
                value=str(item.url),
                key=f"link_url_{i}",
            )

            label = st.text_input(
                "Label",
                value=item.label or "",
                key=f"link_label_{i}",
            )

            professional_links.append(
                {
                    "url": link_url,
                    "kind": item.kind,
                    "label": label or None,
                }
            )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------
    st.divider()

    if st.button(
        "Save & Continue",
        type="primary",
        use_container_width=True,
    ):
        try:
            updated_profile = UserProfile(
                schema_version=profile.schema_version,
                personal_information={
                    "name": name,
                    "email": email or None,
                    "phone": phone or None,
                    "location": location or None,
                },
                professional_summary=professional_summary or None,
                education=education,
                experience=experience,
                skills=[
                    {
                        "name": skill.strip(),
                        "level": None,
                    }
                    for skill in skills_text.split(",")
                    if skill.strip()
                ],
                certifications=certifications,
                projects=projects,
                languages=[
                    language.strip()
                    for language in languages_text.split(",")
                    if language.strip()
                ],
                professional_links=professional_links,
                achievements=profile.achievements,
                volunteering=profile.volunteering,
                review_status="approved",
            )

            st.session_state["profile"] = updated_profile.model_dump(
                mode="json"
            )

            st.success("Profile saved successfully.")
            return updated_profile

        except ValidationError as e:
            st.error("Please check the profile fields.")
            st.code(str(e))

    return None