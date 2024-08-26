import os
import streamlit as st

def sidebar():
    st.sidebar.markdown("### Configuration")
    st.sidebar.markdown("Please provide the following keys to evaluate LLM response:")
    st.sidebar.info("Keys defined in your environment variables are automatically loaded.")

    # OpenAI API Key
    st.sidebar.markdown("You can find the OpenAI API Key [here](https://platform.openai.com/account/api-keys).")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", key="openai_key", type="password", value=os.getenv("OPENAI_API_KEY", default=""))
    os.environ["OPENAI_API_KEY"] = openai_api_key

    # Serper API Key
    st.sidebar.markdown("You can find the Serper API Key [here](https://serpapi.com/dashboard).")
    serper_api_key = st.sidebar.text_input("Serper API Key", key="serper_key", type="password", value=os.getenv("SERPER_API_KEY", default=""))
    os.environ["SERPER_API_KEY"] = serper_api_key

    # ScraperAPI Key
    st.sidebar.markdown("You can find the ScraperAPI Key [here](https://www.scraperapi.com/).")
    scraper_api_key = st.sidebar.text_input("ScraperAPI Key", key="scraper_key", type="password", value=os.getenv("SCRAPER_API_KEY", default=""))
    os.environ["SCRAPER_API_KEY"] = scraper_api_key
