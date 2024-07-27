import re
import time
import pandas as pd
import streamlit as st

from openfactcheck.core.base import OpenFactCheck
from openfactcheck.app.utils import style_metric_cards

# Create a function to check a LLM response
def evaluate_response(ofc: OpenFactCheck):
    """
    This function creates a Streamlit app to evaluate the factuality of a LLM response.
    """
    if 'response' not in st.session_state:
        st.session_state.response = None

    # Initialize the solvers
    claimprocessors = ofc.list_claimprocessors()
    retrievers = ofc.list_retrievers()
    verifiers = ofc.list_verifiers()

    st.write("This is where you can check factuality of a LLM response.")

    # Customize FactChecker
    st.write("Customize FactChecker")

    # Dropdown in three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        claimprocessor = st.selectbox("Select Claim Processor", list(claimprocessors))
    with col2:
        retriever = st.selectbox("Select Retriever", list(retrievers))
    with col3:
        verifier = st.selectbox("Select Verifier", list(verifiers))

    # Input
    input_text = {"text": st.text_area("Enter LLM response here", "This is a sample LLM response.")}

    # Button to check factuality
    if st.button("Check Factuality"):
        with st.status("Checking factuality...", expanded=True) as status:
            # Configure the pipeline
            st.write("Configuring pipeline...")
            ofc.init_pipeline_manually([claimprocessor, retriever, verifier])
            st.write("Pipeline configured...")

            # Evaluate the response
            st.write("Evaluating response...")

            response = ofc(input_text, stream=True)
            st.write("Response evaluated...")

            status.update(label="Factuality checked...", state="complete", expanded=False)

        # Display pipeline configuration
        pipeline_str = "&nbsp;&nbsp;&nbsp;┈➤&nbsp;&nbsp;&nbsp;".join([claimprocessor, retriever, verifier])
        st.info(f"""**Pipeline**:&nbsp;&nbsp;&nbsp; \n{pipeline_str}""")

        # Store the final response in the session state
        st.session_state.final_response = None

        col1, col2 = st.columns([3, 1])
        with col1:
            def process_stream(responses):
                """
                Process each response from the stream as a simulated chat output.
                This function yields each word from the formatted text of the response,
                adding a slight delay to simulate typing in a chat.
                """

                for response in responses:
                    if "claimprocessor" in response["solver_name"]:
                        # Extract response details
                        output_text = response["output"]

                        # Get the number of detected claims
                        detected_claims = output_text.get("claims", [])

                        def extract_text(claim):
                            """
                            Extracts text from a claim that might be a string formatted as a dictionary.
                            """
                            # Try to extract text using regular expression if claim is a string formatted as a dictionary
                            match = re.search(r"'text': '([^']+)'", claim)
                            if match:
                                return match.group(1)
                            return claim  # Return as is if no dictionary format detected

                        # Generate formatted text with enumerated claims in Markdown format
                        formatted_text = "#### Detected Claims\n" + "\n".join(f"{i}. {extract_text(claim)}" for i, claim in enumerate(detected_claims, start=1)) + "\n"

                        with col2:
                            st.metric(label="Detected Claims", value=len(detected_claims))
                            style_metric_cards(background_color="#F0F0F0", border_color="#F0F0F0", border_radius_px=0)

                        # Yield each word with a space and simulate typing by sleeping
                        for word in formatted_text.split(" "):
                            yield word + " "
                            time.sleep(0.01)

                        st.session_state.claimprocessor_flag = True

                    elif "retriever" in response["solver_name"]:
                        # Extract response details
                        output_text = response["output"]

                        evidences = []
                        for _, claim_with_evidences in output_text.get("claims_with_evidences", {}).items():
                            for evidence in claim_with_evidences:
                                evidences.append(evidence[1])

                        # Generate formatted text with enumerated evidences in Markdown format
                        formatted_text = "#### Retrieved Evidences\n" + "\n".join(f"{i}. {evidence}" for i, evidence in enumerate(evidences, start=1))

                        with col2:
                            st.metric(label="Retrieved Evidences", value=len(evidences))
                            style_metric_cards(background_color="#F0F0F0", border_color="#F0F0F0", border_radius_px=0)

                        # Yield each word with a space and simulate typing by sleeping
                        for word in formatted_text.split(" "):
                            yield word + " "
                            time.sleep(0.01)

                    elif "verifier" in response["solver_name"]:
                        # Extract response details
                        output_text = response["output"]

                        # Store the final response in the session state
                        st.session_state.final_response = output_text

                        # Yield each word with a space and simulate typing by sleeping
                        for word in formatted_text.split(" "):
                            yield word + " "
                            time.sleep(0.01)

            st.write_stream(process_stream(response))

            # Process the final response
            final_response = st.session_state.final_response
            if final_response is not None:
                overall_factuality = final_response.get("label", "Unknown")
                with col2:
                    if overall_factuality == True:
                        st.metric(label="Overall Factuality", value="True")
                        style_metric_cards(background_color="#D4EDDA", border_color="#D4EDDA", border_radius_px=0, border_left_color="#28A745")
                    elif overall_factuality == False:
                        st.metric(label="Overall Factuality", value="False")
                        style_metric_cards(background_color="#F8D7DA", border_color="#F8D7DA", border_radius_px=0, border_left_color="#DC3545")

    # Button to reset
    if st.session_state.response is not None:
        if st.button("Reset"):
            st.session_state.response = None
            st.rerun()