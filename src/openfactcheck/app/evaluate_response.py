import os
import re
import time
import pandas as pd
import streamlit as st

from openfactcheck.base import OpenFactCheck
from openfactcheck.app.utils import metric_card

def extract_text(claim):
    """
    Extracts text from a claim that might be a string formatted as a dictionary.
    """
    # Try to extract text using regular expression if claim is a string formatted as a dictionary
    match = re.search(r"'text': '([^']+)'", claim)
    if match:
        return match.group(1)
    return claim  # Return as is if no dictionary format detected

# Create a function to check a LLM response
def evaluate_response(ofc: OpenFactCheck):
    """
    This function creates a Streamlit app to evaluate the factuality of a LLM response.
    """

    # Initialize the response_evaluator
    response_evaluator = ofc.ResponseEvaluator

    # Initialize the solvers
    st.session_state.claimprocessors = ofc.list_claimprocessors()
    st.session_state.retrievers = ofc.list_retrievers()
    st.session_state.verifiers = ofc.list_verifiers()

    st.write("This is where you can check factuality of a LLM response.")

    # Customize FactChecker
    st.write("Customize FactChecker")

    # Dropdown in three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        if "claimprocessor" not in st.session_state:
            st.session_state.claimprocessor = st.selectbox("Select Claim Processor", list(st.session_state.claimprocessors))
        else:
            st.session_state.claimprocessor = st.selectbox("Select Claim Processor", list(st.session_state.claimprocessors), index=list(st.session_state.claimprocessors).index(st.session_state.claimprocessor))
    with col2:
        if "retriever" not in st.session_state:
            st.session_state.retriever = st.selectbox("Select Retriever", list(st.session_state.retrievers))
        else:
            st.session_state.retriever = st.selectbox("Select Retriever", list(st.session_state.retrievers), index=list(st.session_state.retrievers).index(st.session_state.retriever))
    with col3:
        if "verifier" not in st.session_state:
            st.session_state.verifier = st.selectbox("Select Verifier", list(st.session_state.verifiers))
        else:
            st.session_state.verifier = st.selectbox("Select Verifier", list(st.session_state.verifiers), index=list(st.session_state.verifiers).index(st.session_state.verifier))

    # Input
    if "input_text" not in st.session_state:
        st.session_state.input_text = {"text": st.text_area("Enter LLM response here", "This is a sample LLM response.")}
    else:
        st.session_state.input_text = {"text": st.text_area("Enter LLM response here", st.session_state.input_text["text"])}

    # Button to check factuality
    if st.button("Check Factuality"):
        with st.status("Checking factuality...", expanded=True) as status:
            # Configure the pipeline
            st.write("Configuring pipeline...")
            ofc.init_pipeline_manually([st.session_state.claimprocessor, st.session_state.retriever, st.session_state.verifier])
            st.write("Pipeline configured...")

            # Evaluate the response
            st.write("Evaluating response...")

            response = response_evaluator.evaluate_streaming(st.session_state.input_text)
            st.write("Response evaluated...")

            status.update(label="Factuality checked...", state="complete", expanded=False)

        # Display pipeline configuration
        pipeline_str = "&nbsp;&nbsp;&nbsp;┈➤&nbsp;&nbsp;&nbsp;".join([st.session_state.claimprocessor, st.session_state.retriever, st.session_state.verifier])
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

                        # Generate formatted text with enumerated claims in Markdown format
                        formatted_text = "### Detected Claims\n"
                        formatted_text += "\n".join(f"{i}. {extract_text(claim)}" for i, claim in enumerate(detected_claims, start=1))
                        formatted_text += "\n"

                        with col2:
                            metric_card(label="Detected Claims", value=len(detected_claims))

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

                        # # Generate formatted text with enumerated evidences in Markdown format
                        # formatted_text = "#### Retrieved Evidences\n"
                        # formatted_text += "\n".join(f"{i}. {evidence}" for i, evidence in enumerate(evidences, start=1))
                        # formatted_text += "\n"

                        with col2:
                            metric_card(label="Retrieved Evidences", value=len(evidences))

                        # # Yield each word with a space and simulate typing by sleeping
                        # for word in formatted_text.split(" "):
                        #     yield word + " "
                        #     time.sleep(0.01)

                    elif "verifier" in response["solver_name"]:
                        # Extract response details
                        output_text = response["output"]

                        # Get detail
                        details = output_text.get("detail", None)
                        if details is None:
                            detail_text = "The verifier did not provide any detail. Please use other verifiers for more information."
                        else:
                            detail_text = ""

                            # Apply color to the claim based on factuality
                            claims=0
                            false_claims = 0
                            true_claims = 0
                            controversial_claims = 0
                            unverified_claims = 0
                            for i, detail in enumerate(details):
                                # Get factuality information
                                factuality = str(detail.get("factuality", None))
                                if factuality is not None:
                                    claim=detail.get("claim", "")
                                    if factuality == "-1" or factuality == "False":
                                        detail_text += f'##### :red[{str(i+1) + ". " + extract_text(claim)}]'
                                        detail_text += "\n"
                                        claims += 1
                                        false_claims += 1
                                    elif factuality == "1" or factuality == "True":
                                        detail_text += f'##### :green[{str(i+1) + ". " + extract_text(claim)}]'
                                        detail_text += "\n"
                                        claims += 1
                                        true_claims += 1
                                    elif factuality == "0":
                                        detail_text += f'##### :orange[{str(i+1) + ". " + extract_text(claim)}]'
                                        detail_text += "\n"
                                        claims += 1
                                        controversial_claims += 1
                                    else:
                                        detail_text += f'##### :purple[{str(i+1) + ". " + extract_text(claim)}]'
                                        detail_text += "\n"
                                        claims += 1
                                        unverified_claims += 1
                                else:
                                    st.error("Factuality not found in the verifier output.")

                                # Add error information
                                if detail.get("error", None) is not "None":
                                    detail_text += f"- **Error**: {detail.get('error', '')}"
                                    detail_text += "\n"

                                # Add reasoning information
                                if detail.get("reasoning", None) is not "None":
                                    detail_text += f"- **Reasoning**: {detail.get('reasoning', '')}"
                                    detail_text += "\n"
                                
                                # Add correction
                                if detail.get("correction", None) is not "":
                                    detail_text += f"- **Correction**: {detail.get('correction', '')}"
                                    detail_text += "\n"

                                # Add evidence
                                if detail.get("evidence", None) is not "":
                                    evidence_text = ""
                                    for evidence in detail.get("evidences", []):
                                        evidence_text += f"  - {evidence[1]}"
                                        evidence_text += "\n"
                                    detail_text += f"- **Evidence**:\n{evidence_text}"

                                        
                        # Generate formatted text with the overall factuality in Markdown format
                        formatted_text = "### Factuality Detail\n"
                        formatted_text += "Factuality of each claim is color-coded (:red[red means false], :green[green means true], :orange[orange means controversial], :violet[violet means unverified]).\n"
                        formatted_text += f"{detail_text}\n"
                        formatted_text += "\n"

                        # Get the number of true and false claims
                        with col2:
                            metric_card(label="Supported Claims", value=true_claims, background_color="#D1ECF1", border_left_color="#17A2B8")
                            metric_card(label="Conflicted Claims", value=false_claims, background_color="#D1ECF1", border_left_color="#17A2B8")
                            metric_card(label="Controversial Claims", value=controversial_claims, background_color="#D1ECF1", border_left_color="#17A2B8")
                            metric_card(label="Unverified Claims", value=unverified_claims, background_color="#D1ECF1", border_left_color="#17A2B8")
                        
                        # Get overall factuality (label)
                        overall_factuality = output_text.get("label", "Unknown")
                        with col2:
                            with st.container():
                                if overall_factuality == True:
                                    metric_card(label="Overall Factuality", value="True", background_color="#D4EDDA", border_left_color="#28A745")
                                elif overall_factuality == False:
                                    metric_card(label="Overall Factuality", value="False", background_color="#F8D7DA", border_left_color="#DC3545")

                        # Get overall credibility (score)
                        overall_credibility = true_claims / claims if claims > 0 else 0
                        with col2:
                            if overall_credibility > 0.75 and overall_credibility <= 1:
                                # Green background
                                metric_card(label="Overall Credibility", value=f"{overall_credibility:.2%}", background_color="#D4EDDA", border_left_color="#28A745")
                            elif overall_credibility > 0.25 and overall_credibility <= 0.75:
                                # Yellow background
                                metric_card(label="Overall Credibility", value=f"{overall_credibility:.2%}", background_color="#FFF3CD", border_left_color="#FFC107")
                            else:
                                # Red background
                                metric_card(label="Overall Credibility", value=f"{overall_credibility:.2%}", background_color="#F8D7DA", border_left_color="#DC3545")

                        # Yield each word with a space and simulate typing by sleeping
                        for word in formatted_text.split(" "):
                            yield word + " "
                            time.sleep(0.01)

            st.write_stream(process_stream(response))
                            