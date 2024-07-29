import argparse
import streamlit as st
from streamlit_option_menu import option_menu

from openfactcheck.core.base import OpenFactCheck, OpenFactCheckConfig
from openfactcheck.app.sidebar import sidebar
from openfactcheck.app.evaluate_response import evaluate_response
from openfactcheck.app.utils import footer

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
    def __init__(self):
        pass

    def run(self, config_path: str = "config.json"):
        # Initialize OpenFactCheck
        config = OpenFactCheckConfig(config_path)
        ofc = OpenFactCheck(config)

        # Set up Dashboard
        st.set_page_config(page_title="OpenFactCheck Dashboard", 
                        page_icon=":bar_chart:", 
                        layout="wide",
                        initial_sidebar_state="collapsed")
        
        # Set up footer
        footer("Copyright © 2024 MBZUAI | Made with ❤︎ by OpenFactCheck Team")

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

        # Load the selected page
        if selected == "Evaluate LLM Response":
            st.info("Please provide OpenAI API Key, Serper API Key and Azure Search Key in the sidebar to evaluate LLM response.")
            evaluate_response(ofc)
        # elif selected == "Evaluate LLM":
        #     evaluate_llm()
        # elif selected == "Evaluate FactChecker":
        #     evaluate_factchecker()
        # elif selected == "Leaderboards":
        #     leaderboards()
        # else:
        #     about()


if __name__ == "__main__":
    args = parse_args()

    app = App()
    app.run(args.config_path)