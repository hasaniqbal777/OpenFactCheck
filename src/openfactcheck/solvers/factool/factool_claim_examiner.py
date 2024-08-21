import json

from .factool_utils.chat_api import OpenAIChat
from .factool_utils.prompt import VERIFICATION_PROMPT

from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("factool_claim_examiner", "evidences", "claim_info")
class FactoolClaimExaminer(StandardTaskSolver):
    """
    A solver to examine the claims in a response.
    """
    def __init__(self, args):
        super().__init__(args)
        self.model_name = self.global_config.get("model_name", "gpt-4o")
        self.path_save_stance = args.get("path_save_stance", "evidence_stance.json")
        self.verifications = None
        self.gpt = OpenAIChat(self.model_name)
        self.verification_prompt = VERIFICATION_PROMPT

    # async def coro (self, factool_instance, claims_in_response, evidences):
    #    self.verifications = await factool_instance.pipelines["kbqa_online"]._verification(claims_in_response, evidences)
    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claim_info = state.get(self.input_name)
        # Recover the Factool objects
        claims_in_response = []
        queires = []
        search_outputs_for_claims = []
        for key, pair in claim_info.items():
            claim = key or pair["claim"]
            claims_in_response.append({"claim": claim})
            queires.append(pair["automatic_queries"])
            search_outputs_for_claim = []
            for evidence in pair["evidence_list"]:
                search_outputs_for_claim.append(
                    {
                        "content": evidence["web_page_snippet_manual"],
                        "source": evidence["url"],
                    }
                )
            search_outputs_for_claims.append(search_outputs_for_claim)

        claims_with_evidences = {k: [u['web_page_snippet_manual'] for u in claim_info[k]['evidence_list']] for k in
                                 claim_info.keys()}
        verifications = self._verification(claims_with_evidences)

        # evidences = [
        #     [output["content"] for output in search_outputs_for_claim]
        #     for search_outputs_for_claim in search_outputs_for_claims
        # ]

        # Attach the verifications (stances) to the claim_info
        for index, (key, pair) in enumerate(claim_info.items()):
            # print(f'Verifications: {verifications}\n')
            # print(f'Verification for claim {key}: Index {index}\n')
            # print(f'Verification for claim {key}: {verifications[index]}\n')
            # print(f'Verification for claim {key}: Type = {type(verifications[index])}\n')
            stance = ""
            index = 0  # Ensure the 'index' variable is defined somewhere appropriate in your context

            # Check if verifications at the current index is None or 'None'
            if verifications[index] is None or verifications[index] == "None":
                stance = claims_in_response[index]["claim"]
            else:
                # Initialize stance with error or empty string
                error = verifications[index].get("error", "")
                if error and error != "None":
                    stance = error + " "
                
                # Append reasoning if it exists and is not 'None'
                reasoning = verifications[index].get("reasoning", "")
                if reasoning and reasoning != "None":
                    stance += reasoning
                
                # Append claim or correction if available
                correction = verifications[index].get("correction", "")
                if correction and correction != "None":
                    stance += " " + correction
                else:
                    stance += claims_in_response[index]["claim"]
            claim_info[key]["stances"] = [stance]
            for j in range(len(claim_info[key]["evidence_list"])):
                claim_info[key]["evidence_list"][j]["stance"] = stance

        # write to json file
        # Serializing json
        json_object = json.dumps(claim_info, indent=4)

        # Writing to sample.json
        with open(self.path_save_stance, "w") as outfile:
            outfile.write(json_object)

        state.set(self.output_name, claim_info)
        return True, state

    def _verification(self, claims_with_evidences):
        messages_list = [
            [
                {"role": "system", "content": self.verification_prompt['system']},
                {"role": "user", "content": self.verification_prompt['user'].format(
                    claim=claim,
                    evidence=str([e[1] for e in evidence if isinstance(e, (list, tuple)) and len(e) > 1])
                )}
            ]
            for claim, evidence in claims_with_evidences.items()
        ]
        return self.gpt.run(messages_list, dict)
