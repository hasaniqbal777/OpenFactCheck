import os
import streamlit as st

@st.dialog("Secrets Configuration")
def get_secrets():
    st.markdown("Please provide the following keys to evaluate LLM response:")
    st.info("Keys defined in your environment variables are automatically loaded.")

    # OpenAI API Key
    st.markdown("You can find the OpenAI API Key [here](https://platform.openai.com/account/api-keys).")
    openai_api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", default=""))
    os.environ["OPENAI_API_KEY"] = openai_api_key

    # Serper API Key
    st.markdown("You can find the Serper API Key [here](https://serpapi.com/dashboard).")
    serper_api_key = st.text_input("Serper API Key", type="password", value=os.getenv("SERPER_API_KEY", default=""))
    os.environ["SERPER_API_KEY"] = serper_api_key

    # ScraperAPI Key
    st.markdown("You can find the ScraperAPI Key [here](https://www.scraperapi.com/).")
    scraper_api_key = st.text_input("ScraperAPI Key", type="password", value=os.getenv("SCRAPER_API_KEY", default=""))
    os.environ["SCRAPER_API_KEY"] = scraper_api_key

    if st.button("Submit"):
        st.session_state.api_keys = True
        st.rerun()
