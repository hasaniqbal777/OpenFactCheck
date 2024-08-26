import os
import argparse
import streamlit as st
from streamlit_option_menu import option_menu

from openfactcheck import OpenFactCheck
from openfactcheck.lib import OpenFactCheckConfig
from openfactcheck.app.sidebar import sidebar
from openfactcheck.app.dialogs import get_secrets
from openfactcheck.app.evaluate_response import evaluate_response
from openfactcheck.app.evaluate_llm import evaluate_llm
from openfactcheck.app.evaluate_factchecker import evaluate_factchecker

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize OpenFactCheck with custom configuration.')
    
    # Add arguments here, example:
    parser.add_argument("--config-path", 
                        type=str, 
                        help="Config File Path",
                        default="config.json")
    
    # Parse arguments from command line
    args = parser.parse_args()
    return args
    
class App:
    def __init__(self, config_path: str = "config.json"):
        # Set up Dashboard
        st.set_page_config(page_title="OpenFactCheck Dashboard", 
                        page_icon=":bar_chart:", 
                        layout="wide",
                        initial_sidebar_state="collapsed")
        
        # Get API Keys
        st.session_state.api_keys = False
        # Check if the API keys are already set in the environment variables
        if os.getenv("OPENAI_API_KEY") and os.getenv("SERPER_API_KEY") and os.getenv("SCRAPER_API_KEY"):
            st.session_state.api_keys = True
        else:
            get_secrets()
        
        # Initialize OpenFactCheck
        @st.cache_resource(show_spinner=False)
        def init(config_path: str = "config.json"):
            # Initialize OpenFactCheckConfig
            config = OpenFactCheckConfig(config_path)
            ofc = OpenFactCheck(config)

            return ofc
        
        if st.session_state.api_keys:
            self.ofc = init(config_path)
        else:
            self.ofc = None

    def run(self):
        # Set up Sidebar
        sidebar()
                        
        # Title
        st.markdown("<h1 style='text-align: center;'>OpenFactCheck Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<h5 style='text-align: center;'>An Open-source Factuality Evaluation Demo for LLMs</h5>", unsafe_allow_html=True)

        # Selection Menu
        selected = option_menu(None, ["Evaluate LLM Response", "Evaluate LLM", "Evaluate FactChecker", "Leaderboards", "About"], 
            icons=['card-checklist', 'check-square', "check2-all", "trophy", "info-circle"],
            menu_icon="cast", 
            default_index=0, 
            orientation="horizontal"
        )

        # Check if API keys are set
        if not st.session_state.api_keys:
            st.warning("Please provide the necessary API keys to proceed.")
            return

        # Load the selected page
        if selected == "Evaluate LLM Response":
            evaluate_response(self.ofc)
        elif selected == "Evaluate LLM":
            evaluate_llm(self.ofc)
        elif selected == "Evaluate FactChecker":
            evaluate_factchecker(self.ofc)
        # elif selected == "Leaderboards":
        #     leaderboards()
        # else:
        #     about()


if __name__ == "__main__":
    args = parse_args()

    app = App(args.config_path)
    app.run()