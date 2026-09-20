import streamlit as st


def portfolio_section():
    st.subheader("Add your portfolio")

    st.write(
        "Add your personal portfolio website to help "
        "CareerCompass understand your projects and experience."
    )

    portfolio_url = st.text_input(
        "Portfolio URL",
        placeholder="https://yourportfolio.com",
        key="portfolio_url",
    )

    if portfolio_url:
        if not portfolio_url.startswith(("http://", "https://")):
            st.error(
                "Please enter a valid URL starting with "
                "http:// or https://"
            )
            return None

        st.success("Portfolio URL added successfully.")

    return portfolio_url