import os
import uuid
import zipfile
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from importlib import resources as pkg_resources

from openfactcheck.app.utils import metric_card

from openfactcheck import OpenFactCheck
from openfactcheck.templates import factchecker as templates_dir

# Import solver configuration templates
claims_templates_path = str(pkg_resources.files(templates_dir) / "claims.jsonl")
documents_templates_path = str(pkg_resources.files(templates_dir) / "documents.jsonl")

def evaluate_factchecker(ofc: OpenFactCheck):
    """
    This function creates a Streamlit app to evaluate a Factchecker.
    """
    
    # Initialize the FactChecker Evaluator
    fc_evaluator = ofc.FactCheckerEvaluator

    st.write("This is where you can evaluate the factuality of a FactChecker.")

    # Display the instructions
    st.write("Download the benchmark evaluate the factuality of a FactChecker.")

    # Check if the file exists
    if os.path.exists(claims_templates_path) and os.path.exists(documents_templates_path):
        # Create a ZIP file in memory
        from io import BytesIO
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Define the name of the file within the ZIP archive
            zip_path = os.path.basename(claims_templates_path) # 'claims.jsonl'
            # Add file to the ZIP file
            zf.write(claims_templates_path, arcname=zip_path)

            # TODO: documents.jsonl functionality is still in development
            # zip_path = os.path.basename(documents_templates_path) # 'documents.jsonl'
            # # Add file to the ZIP file
            # zf.write(documents_templates_path, arcname=zip_path)
        
        # Reset pointer to start of the memory file
        memory_file.seek(0)

        # Create a download button and the file will be downloaded when clicked
        btn = st.download_button(
            label="Download",
            data=memory_file,
            file_name="openfactcheck_factchecker_benchmark.zip",
            mime="application/zip"
        )
    else:
        st.error("File not found.")

    # Display the instructions
    st.write("Upload the FactChecker responses as a JSON file below to evaluate the factuality.")

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

    def update_first_name():
        st.session_state.first_name = st.session_state.input_first_name

    def update_last_name():
        st.session_state.last_name = st.session_state.input_last_name

    def update_email():
        st.session_state.email = st.session_state.input_email

    def update_organization():
        st.session_state.organization = st.session_state.input_organization

    def update_factchecker():
        st.session_state.factchecker = st.session_state.input_factchecker

    def update_include_in_leaderboard():
        st.session_state.include_in_leaderboard = st.session_state.input_include_in_leaderboard

    # Display instructions
    st.write("Please provide the following information to be included in the leaderboard.")

    # Create text inputs to enter the user information
    st.session_state.id = uuid.uuid4().hex
    st.text_input("First Name", key="input_first_name", on_change=update_first_name)
    st.text_input("Last Name", key="input_last_name", on_change=update_last_name)
    st.text_input("Email", key="input_email", on_change=update_email)
    st.text_input("FactChecker Name", key="input_factchecker", on_change=update_factchecker)
    st.text_input("Organization (Optional)", key="input_organization", on_change=update_organization)

    st.checkbox("Please check this box if you want your FactChecker to be included in the leaderboard.", 
                key="input_include_in_leaderboard", 
                on_change=update_include_in_leaderboard)

    if st.button("Evaluate FactChecker"):
        # Display a success message
        st.success("User information saved successfully.")

        # Display a waiting message
        with st.status("Evaluating factuality of the FactChecker...", expanded=True) as status:
            result = fc_evaluator.evaluate(input_path=uploaded_data, eval_type="claims")
            status.update(label="FactChecker evaluated...", state="complete", expanded=False)

        # Display the evaluation report
        st.write("### Evaluation report:")
        
        col1, col2 = st.columns(2, gap="large")
        with col1:
            # Create the heatmap
            classes = ['True', 'False']
            fig = plt.figure()
            sns.heatmap(fc_evaluator.confusion_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
            plt.ylabel('Actual Class')
            plt.xlabel('Predicted Class')
            st.pyplot(fig)
        with col2:
            # Display the metrics
            accuracy = fc_evaluator.results["True_as_positive"]["accuracy"]
            if accuracy > 0.75 and accuracy <= 1:
                # Green background
                metric_card(label="Accuracy", value=f"{accuracy:.2%}", background_color="#D4EDDA", border_left_color="#28A745")
            elif accuracy > 0.25 and accuracy <= 0.75:
                # Yellow background
                metric_card(label="Accuracy", value=f"{accuracy:.2%}", background_color="#FFF3CD", border_left_color="#FFC107")
            else:
                # Red background
                metric_card(label="Accuracy", value=f"{accuracy:.2%}", background_color="#F8D7DA", border_left_color="#DC3545")
                
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:  
                metric_card(label="Total Time", value=fc_evaluator.results["total_time"])
            with sub_col2:
                metric_card(label="Total Cost", value=fc_evaluator.results["total_cost"])
            with sub_col3:
                metric_card(label="Number of Samples", value=fc_evaluator.results["num_samples"])

            st.text("Report:\n" + fc_evaluator.classification_report)
        

    