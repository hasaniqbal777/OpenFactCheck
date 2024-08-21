import json

from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("factool_blackbox_post_editor", "claim_info", "claim_info")
class FactoolBlackboxPostEditor(StandardTaskSolver):
    """
    A solver to post-process the results of the Factool black box model.
    Used to presents the results in human-readable format and to save the analysis in a JSON file.
    """
  
    def __init__(self, args):
        super().__init__(args)
        self.path_save_analysis = args.get("path_save_analysis","factool_evidence_analysis.json")

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claim_info = state.get(self.input_name)

        # Restructure some of the output for concatenation (corrected claims)
        edited_claims = ''
        for clf in claim_info['detailed_information'][0]['claim_level_factuality']:
            edited_claims += 'Claim: "' + clf['claim'] + '" => '
            edited_claims += ('' if (clf['error'] == 'None' or len(clf['error']) == 0) else (clf['error'] + ' '))
            edited_claims += ('' if (clf['reasoning'] == 'None' or len(clf['reasoning']) == 0) else clf['reasoning'])
            edited_claims += ((' ' + clf['claim']) if (clf['correction'] == 'None' or len(clf['correction']) == 0) else (' ' + clf['correction']))
            edited_claims += '\n'
        edited_claims = edited_claims[:-1]
        new_claim_info = {}
        new_claim_info[claim_info['detailed_information'][0]['response']] = {
            "edited_claims": edited_claims
        }

        # Serializing json
        json_object = json.dumps(claim_info, indent=4)

        # Writing to sample.json
        with open(self.path_save_analysis, "w") as outfile:
            outfile.write(json_object)

        state.set(self.output_name, new_claim_info)
        return True, state
