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
    st.session_state.claimprocessors = {
        "Factool ClaimProcessor": "factool_claimprocessor",
        "FactCheckGPT ClaimProcessor": "factcheckgpt_claimprocessor",
        "UrduFactCheck ClaimProcessor": "urdufactcheck_claimprocessor",
    }
    st.session_state.retrievers = {
        "Factool Retriever": "factool_retriever",
        "FactCheckGPT Retriever": "factcheckgpt_retriever",
        "UrduFactCheck Retriever": "urdufactcheck_retriever",
        "UrduFactCheck Translator Retriever": "urdufactcheck_translator_retriever",
        "UrduFactCheck Thresholded Translator Retriever": "urdufactcheck_thresholded_translator_retriever",
    }
    st.session_state.verifiers = {
        "FactCheckGPT Verifier": "factcheckgpt_verifier",
        "Factool Verifier": "factool_verifier",
        "UrduFactCheck Verifier": "urdufactcheck_verifier",
    }
    st.session_state.claimprocessor = "Factool ClaimProcessor"
    st.session_state.retriever = "Factool Retriever"
    st.session_state.verifier = "FactCheckGPT Verifier"

    st.info(
        "Customize an automatic fact-checker and verify the factuality free-form text. You can select a *claimprocessor*, *retriever*, and *verifier* from the dropdowns below."
    )

    # Dropdown in three columns
    col1, col2, col3 = st.columns(3)
    with col1:
        if "claimprocessor" not in st.session_state:
            claimprocessor_choice = st.selectbox(
                "Select Claim Processor",
                list(st.session_state.claimprocessors.keys()),
                help="Select a claim processor to use for processing claims.",
            )
            st.session_state.claimprocessor = st.session_state.claimprocessors[claimprocessor_choice]
        else:
            claimprocessor_choice = st.selectbox(
                "Select Claim Processor",
                list(st.session_state.claimprocessors.keys()),
                index=list(st.session_state.claimprocessors).index(st.session_state.claimprocessor),
                help="Select a claim processor to use for processing claims.",
            )
            st.session_state.claimprocessor = st.session_state.claimprocessors[claimprocessor_choice]
    with col2:
        if "retriever" not in st.session_state:
            retriever_choice = st.selectbox(
                "Select Retriever",
                list(st.session_state.retrievers.keys()),
                help="Select a retriever to use for retrieving evidences.",
            )
            st.session_state.retriever = st.session_state.retrievers[retriever_choice]
        else:
            retriever_choice = st.selectbox(
                "Select Retriever",
                list(st.session_state.retrievers.keys()),
                index=list(st.session_state.retrievers.keys()).index(st.session_state.retriever),
                help="Select a retriever to use for retrieving evidences.",
            )
            st.session_state.retriever = st.session_state.retrievers[retriever_choice]
    with col3:
        if "verifier" not in st.session_state:
            verifier_choice = st.selectbox(
                "Select Verifier",
                list(st.session_state.verifiers.keys()),
                help="Select a verifier to use for verifying claims.",
            )
            st.session_state.verifier = st.session_state.verifiers[verifier_choice]
        else:
            verifier_choice = st.selectbox(
                "Select Verifier",
                list(st.session_state.verifiers.keys()),
                index=list(st.session_state.verifiers.keys()).index(st.session_state.verifier),
                help="Select a verifier to use for verifying claims.",
            )
            st.session_state.verifier = st.session_state.verifiers[verifier_choice]

    # Your sample responses
    sample_responses = [
        "Elon Musk bought Twitter in 2020 and renamed it to X.",
        "Burj Khalifa is the tallest building in the world and is located in Abu Dhabi. I took a photo in front of it.",
        "برج خلیفہ دنیا کی بلند ترین عمارت ہے اور ابوظہبی میں واقع ہے۔ میں نے اس کے سامنے تصویر کھینچی۔",
    ]

    # Initialize the state for 'input_text' if not already there
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    # 3. Define a callback to cycle through responses
    def load_sample():
        current = st.session_state.input_text
        try:
            idx = sample_responses.index(current)
            next_idx = (idx + 1) % len(sample_responses)
        except ValueError:
            next_idx = 0
        st.session_state.input_text = sample_responses[next_idx]

    # 4. Render the textarea, binding it to st.session_state["input_text"]
    st.text_area(
        "Enter LLM response here",
        key="input_text",
        height=150,
        placeholder="Type or paste your free-form text here...",
    )

    # 5. Render the button with on_click=load_sample
    col1, col2 = st.columns([1, 3])
    with col2:
        st.button(
            "Load Sample Response",
            on_click=load_sample,
            use_container_width=True,
            type="secondary",
        )

    with col1:
        # Button to check factuality
        check = st.button("Check Factuality", use_container_width=True, type="primary")

    # Check if the button is clicked
    if check:
        with st.status("Checking factuality...", expanded=True) as status:
            # Configure the pipeline
            st.write("Configuring pipeline...")
            ofc.init_pipeline_manually(
                [st.session_state.claimprocessor, st.session_state.retriever, st.session_state.verifier]
            )
            st.write("Pipeline configured...")

            # Evaluate the response
            st.write("Evaluating response...")

            response = response_evaluator.evaluate_streaming(st.session_state.input_text)
            st.write("Response evaluated...")

            status.update(label="Factuality checked...", state="complete", expanded=False)

        # Display pipeline configuration
        pipeline_str = "&nbsp;&nbsp;&nbsp;┈➤&nbsp;&nbsp;&nbsp;".join(
            [st.session_state.claimprocessor, st.session_state.retriever, st.session_state.verifier]
        )
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
                        formatted_text += "\n".join(
                            f"{i}. {extract_text(claim)}" for i, claim in enumerate(detected_claims, start=1)
                        )
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

                        questions = []
                        evidences = []
                        for _, claim_with_evidences in output_text.get("claims_with_evidences", {}).items():
                            for claim_with_evidence in claim_with_evidences:
                                questions.append(claim_with_evidence[0])
                                evidences.append(claim_with_evidence[1])

                        with col2:
                            metric_card(label="Retrieved Evidences", value=len(evidences))

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
                            claims = 0
                            false_claims = 0
                            true_claims = 0
                            controversial_claims = 0
                            unverified_claims = 0
                            for i, detail in enumerate(details):
                                # Get factuality information
                                factuality = str(detail.get("factuality", None))
                                if factuality is not None:
                                    claim = detail.get("claim", "")
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
                                if detail.get("error", None) != "None":
                                    detail_text += f"- **Error**: {detail.get('error', '')}"
                                    detail_text += "\n"

                                # Add reasoning information
                                if detail.get("reasoning", None) != "None":
                                    detail_text += f"- **Reasoning**: {detail.get('reasoning', '')}"
                                    detail_text += "\n"

                                # Add correction
                                if detail.get("correction", None) != "":
                                    detail_text += f"- **Correction**: {detail.get('correction', '')}"
                                    detail_text += "\n"

                                # Add evidence
                                if detail.get("evidences", None) != "":
                                    evidence_text = ""
                                    questions_evidences = {}
                                    for evidence in detail.get("evidences", []):
                                        question_evidence = str(evidence[0].split("?")[0]) + "?"
                                        if question_evidence not in questions_evidences:
                                            questions_evidences[question_evidence] = []
                                        questions_evidences[question_evidence].append(evidence[1])
                                    for question, evidences in questions_evidences.items():
                                        evidence_text += f"- **Evidences against Question**: :orange[{question}]"
                                        evidence_text += "\n"
                                        for evidence in evidences:
                                            evidence_text += f"  - {evidence}\n"
                                    detail_text += evidence_text

                        # Generate formatted text with the overall factuality in Markdown format
                        formatted_text = "### Factuality Detail\n"
                        formatted_text += "Factuality of each claim is color-coded (:red[red means false], :green[green means true], :orange[orange means controversial], :violet[violet means unverified]).\n"
                        formatted_text += f"{detail_text}\n"
                        formatted_text += "\n"

                        # Get the number of true and false claims
                        with col2:
                            metric_card(
                                label="Supported Claims",
                                value=true_claims,
                                background_color="#D1ECF1",
                                border_left_color="#17A2B8",
                            )
                            metric_card(
                                label="Conflicted Claims",
                                value=false_claims,
                                background_color="#D1ECF1",
                                border_left_color="#17A2B8",
                            )
                            metric_card(
                                label="Controversial Claims",
                                value=controversial_claims,
                                background_color="#D1ECF1",
                                border_left_color="#17A2B8",
                            )
                            metric_card(
                                label="Unverified Claims",
                                value=unverified_claims,
                                background_color="#D1ECF1",
                                border_left_color="#17A2B8",
                            )

                        # Get overall factuality (label)
                        overall_factuality = output_text.get("label", "Unknown")
                        with col2:
                            with st.container():
                                if overall_factuality:
                                    metric_card(
                                        label="Overall Factuality",
                                        value="True",
                                        background_color="#D4EDDA",
                                        border_left_color="#28A745",
                                    )
                                elif not overall_factuality:
                                    metric_card(
                                        label="Overall Factuality",
                                        value="False",
                                        background_color="#F8D7DA",
                                        border_left_color="#DC3545",
                                    )

                        # Get overall credibility (score)
                        overall_credibility = true_claims / claims if claims > 0 else 0
                        with col2:
                            if overall_credibility > 0.75 and overall_credibility <= 1:
                                # Green background
                                metric_card(
                                    label="Overall Credibility",
                                    value=f"{overall_credibility:.2%}",
                                    background_color="#D4EDDA",
                                    border_left_color="#28A745",
                                )
                            elif overall_credibility > 0.25 and overall_credibility <= 0.75:
                                # Yellow background
                                metric_card(
                                    label="Overall Credibility",
                                    value=f"{overall_credibility:.2%}",
                                    background_color="#FFF3CD",
                                    border_left_color="#FFC107",
                                )
                            else:
                                # Red background
                                metric_card(
                                    label="Overall Credibility",
                                    value=f"{overall_credibility:.2%}",
                                    background_color="#F8D7DA",
                                    border_left_color="#DC3545",
                                )

                        # Yield each word with a space and simulate typing by sleeping
                        for word in formatted_text.split(" "):
                            yield word + " "
                            time.sleep(0.01)

            st.write_stream(process_stream(response))
