import os
import uuid
import zipfile
import pandas as pd
import streamlit as st
from importlib import resources as pkg_resources

from openfactcheck.app.utils import metric_card

from openfactcheck import OpenFactCheck
from openfactcheck.templates import llm as templates_dir

# Import solver configuration templates
questions_templates_path = str(pkg_resources.files(templates_dir) / "questions.csv")

def evaluate_llm(ofc: OpenFactCheck):
    """
    This function creates a Streamlit app to evaluate the factuality of a LLM.
    """
    # Initialize the LLM Evaluator
    llm_evaluator = ofc.LLMEvaluator
    
    st.write("This is where you can evaluate the factuality of a LLM.")

    # Display the instructions
    st.write("Download the questions and instructions to evaluate the factuality of a LLM.")

    # Check if the file exists
    if os.path.exists(questions_templates_path):
        # Create a ZIP file in memory
        from io import BytesIO
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Define the name of the file within the ZIP archive
            zip_path = os.path.basename(questions_templates_path)  # 'questions.csv'
            # Add file to the ZIP file
            zf.write(questions_templates_path, arcname=zip_path)
        
        # Reset pointer to start of the memory file
        memory_file.seek(0)

        # Create a download button and the file will be downloaded when clicked
        btn = st.download_button(
            label="Download",
            data=memory_file,
            file_name="openfactcheck_llm_benchmark.zip",
            mime="application/zip"
        )
    else:
        st.error("File not found.")

    # Display the instructions
    st.write("Upload the model responses as a JSON file below to evaluate the factuality.")

    # Upload the model output
    uploaded_file = st.file_uploader("Upload", type=["csv"], label_visibility="collapsed")

    # Check if the file is uploaded
    if uploaded_file is None:
        st.info("Please upload a CSV file.")
        return
    
    # Check if the file is a CSV file
    if uploaded_file.type != "text/csv":
        st.error("Invalid file format. Please upload a CSV file.")
        return

    # Read the CSV file
    uploaded_data = pd.read_csv(uploaded_file)

    # Ask user to select datasets they want to evaluate on
    st.write("Please select the datasets you want to evaluate the LLM on.")
    datasets = st.multiselect("Select datasets", ["snowballing", "selfaware", "freshqa", "factoolqa", "felm-wk", "factcheck-bench", "factscore-bio"])

    def update_first_name():
        st.session_state.first_name = st.session_state.input_first_name

    def update_last_name():
        st.session_state.last_name = st.session_state.input_last_name

    def update_email():
        st.session_state.email = st.session_state.input_email

    def update_organization():
        st.session_state.organization = st.session_state.input_organization

    def update_llm_model():
        st.session_state.llm_model = st.session_state.input_llm_model

    def update_include_in_leaderboard():
        st.session_state.include_in_leaderboard = st.session_state.input_include_in_leaderboard

    # Display instructions
    st.write("Please provide the following information to be included in the leaderboard.")

    # Create text inputs to enter the user information
    st.session_state.id = llm_evaluator.run_id
    st.text_input("First Name", key="input_first_name", on_change=update_first_name)
    st.text_input("Last Name", key="input_last_name", on_change=update_last_name)
    st.text_input("Email", key="input_email", on_change=update_email)
    st.text_input("LLM Model Name", key="input_llm_model", on_change=update_llm_model)
    st.text_input("Organization (Optional)", key="input_organization", on_change=update_organization)

    # Create a checkbox to include the user in the leaderboard
    st.checkbox("Please check this box if you want your LLM to be included in the leaderboard.", 
                key="input_include_in_leaderboard", 
                on_change=update_include_in_leaderboard)

    if st.button("Evaluate LLM"):
        # Display a success message
        st.success("User information saved successfully.")

        # Display an information message
        st.info(f"""Please wait while we evaluate the factuality of the LLM.
You will be able to download the evaluation report shortly, if you can wait. The report will also be delivered to your email address.
                
Please note your ID {st.session_state.id}, This will be used to track your evaluation.
If the report is not available, please contact the administrator and provide your ID.""")

        # Display a waiting message
        with st.status("Evaluating factuality of the LLM...", expanded=True) as status:
            # Evaluate the LLM
            results = llm_evaluator.evaluate(model_name=st.session_state.llm_model,
                                             input_path=uploaded_data,
                                             datasets=datasets, 
                                             save_report=False)
            
            # Get plots
            st.write("Generating plots...")
            plots = llm_evaluator.generate_plots(save_plots=False)

            # Generate the evaluation report
            st.write("Generating evaluation report...")
            report_path = llm_evaluator.generate_report(report_path=f"{llm_evaluator.output_path}/{llm_evaluator.run_id}")

            status.update(label="LLM evaluated...", state="complete", expanded=False)

        # Display the plots
        st.write("### Evaluation Report")

        # If snowballing dataset is selected
        if "snowballing" in datasets:
            st.write("#### Evaluation on Snowballing Dataset")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.pyplot(plots["snowballing"]["barplot"])
            with col2:
                st.pyplot(plots["snowballing"]["cm"])
            with col3:
                pass

        # If selfaware dataset is selected
        if "selfaware" in datasets:
            st.write("#### Evaluation on SelfAware Dataset")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.pyplot(plots["selfaware"]["barplot"])
            with col2:
                st.pyplot(plots["selfaware"]["cm"])
            with col3:
                pass    
        
        # If freshqa dataset is selected
        if "freshqa" in datasets:
            st.write("#### Evaluation on FreshQA Dataset")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.pyplot(plots["freshqa"]["piechart"])
            with col2:
                pass
            with col3:
                pass   
        
        # If any of the free-text datasets are selected
        if any(dataset in ["factoolqa", "felm-wk", "factcheck-bench", "factscore-bio"] for dataset in datasets):
            st.write("#### Evaluation on Free-Text Datasets")
            st.pyplot(plots["freetext"]["barplot"])
    
        # Generate the evaluation report
        st.write("### Download Evaluation Report")
        st.info("The report will also be sent to your email address.")

        # Load the evaluation report
        if os.path.exists(report_path):
            with open(report_path, "rb") as file:
                report_bytes = file.read()
                
                # Display the download button
                st.download_button(
                    label="Download",
                    data=report_bytes,
                    file_name="llm_evaluation_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("File not found.")



            
