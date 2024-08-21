import os
import re
import pytz
import datetime
import pandas as pd
from openai import OpenAI
import matplotlib.pyplot as plt

class FreshQAEvaluator():
    def __init__(self):
        self.openai_client = OpenAI()
        self.openai_model_name = "gpt-4o-mini"
        self.current_date = datetime.datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%B %d, %Y")
        self.prefix = (
            "Please evaluate the response to a question under strict evaluation, where"
            " no hallucinations, outdated information, or ill-formed answers are"
            " allowed. Please credit the response only if it provides a confident and"
            " definitive answer, or the correct answer can be obviously inferred from"
            " the response. The primary or final answer when standing alone must be"
            " accurate. Any additional information that is provided must not contradict"
            " the primary answer or reshape one's perception of it. For false-premise"
            " questions, the response must point out the presence of a false premise to"
            " receive credit. For answers that involve names of entities (e.g.,"
            " people), complete names or commonly recognized names are expected."
            " Regarding numerical answers, approximate numbers are generally not"
            " accepted unless explicitly included in the ground-truth answers. A"
            " response that contains any hallucination, no matter how minor, will not"
            " receive credit. Furthermore, when the response indicates that the"
            " information might be outdated, we accept it only if it is evident that"
            " the knowledge has not changed (e.g., through common sense or well-known"
            " facts)."
        )

        self.demo_examples = [
            {
                "question": "How old is the world's oldest verified living person?",
                "correct_answers": [
                    "116 years old",
                    "116",
                ],
                "response": (
                    f"As of today {self.current_date}, the most up-to-date and relevant"
                    " information regarding this query is as follows. The oldest"
                    " verified living person is Maria Branyas Morera, who was born"
                    " on March 4, 1907, making her 116 years old."
                ),
                "comment": (
                    "This is a valid question. The primary answer in the response"
                    " (116 years old) is accurate, and all the provided information"
                    " is accurate and up-to-date. Thus, the response is credited."
                ),
                "evaluation": "correct",
            },
            {
                "question": "When did the UK adopt the Euro?",
                "correct_answers": ["The United Kingdom has never adopted the Euro."],
                "response": (
                    "The UK has never adopted the Euro as its official currency. The"
                    " country has retained the British pound sterling (GBP) as its"
                    " currency."
                ),
                "comment": (
                    "The question contains a false premise. The response debunks the"
                    " question's false premise (i.e., it points out that the UK has"
                    " never adopted the Euro), and all the provided information is"
                    " accurate and up-to-date. Thus, the response is credited."
                ),
                "evaluation": "correct",
            },
            {
                "question": (
                    "How much longer will Brittney Griner spend in the Russian prison?"
                ),
                "correct_answers": [
                    "She was released in December 2022 as part of a prisoner swap."
                ],
                "response": (
                    "I'm sorry, but I have no information to suggest that Brittney"
                    " Griner is currently in a Russian prison. As far as I know, she"
                    " is a professional basketball player who currently plays for the"
                    " Phoenix Mercury in the Women's National Basketball Association"
                    " (WNBA). If you have any more information or context, please let"
                    " me know and I'll do my best to help."
                ),
                "comment": (
                    "The question contains a false premise. The response fails to"
                    " debunk the question's false premise by not explicitly stating"
                    " that Brittney Griner was already released. Additionally, the"
                    " response lacks a confident and definitive answer. Thus, the"
                    " response is not credited."
                ),
                "evaluation": "incorrect",
            },
            {
                "question": (
                    "Which language has the third largest population by number of"
                    " native speakers?"
                ),
                "correct_answers": ["English"],
                "response": "1. Mandarin 2. Spanish 3. English",
                "comment": (
                    "This is a valid question. While the correct answer (English) can"
                    " be inferred from the response, the response lacks an explicit"
                    " statement, which is not desirable."
                    " Thus, the response is not credited."
                ),
                "evaluation": "incorrect",
            },
            {
                "question": (
                    "Has Virginia Woolf's novel about the Ramsay family entered the"
                    " public domain in the United States?"
                ),
                "correct_answers": ["Yes"],
                "response": (
                    "1927's To the Lighthouse is in the public domain in the United"
                    " States. The final answer is To the Lighthouse."
                ),
                "comment": (
                    "This is a valid question. While the primary information in the"
                    " response (1927's To the Lighthouse is in the public domain in"
                    " the United States) is accurate, the final answer when standing"
                    ' alone is inaccurate (it should be "Yes" instead of "To the'
                    ' Lighthouse"). Thus, the response is not credited.'
                ),
                "evaluation": "incorrect",
            },
        ]

        self.demo_questions = [ex["question"] for ex in self.demo_examples]
        self.demo_evaluations = []

        self.demo_evaluation_template = (
            "\ncorrect answer(s): {correct_answers}"
            "\nresponse: {response}"
            "\ncomment: {comment}"
            "\nevaluation: {evaluation}"
        )

        self.evaluation_template = (
            "\ncorrect answer(s): {correct_answers}" "\nresponse: {response}" "\ncomment: "
        )

        self.df = pd.DataFrame()

    def call_openai_api(self, prompt, temperature, max_tokens, chat_completions=True):
        """
        Call the OpenAI API to generate responses.
        """

        # Generate prompts for demo examples
        for ex in self.demo_examples:
            demo_evaluation = self.demo_evaluation_template.format(
                question=ex["question"],
                correct_answers=" | ".join(ex["correct_answers"]),
                response=ex["response"],
                comment=ex["comment"],
                evaluation=ex["evaluation"],
            )
            self.demo_evaluations.append(demo_evaluation)

        # Call the OpenAI API to generate responses
        # If chat completions are enabled, use the chat completions endpoint
        if chat_completions:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. Respond as concisely as"
                            f" possible. Knowledge cutoff: {self.current_date}."
                        ),
                    },
                    {"role": "user", "content": "What's today's date?"},
                    {
                        "role": "assistant",
                        "content": f"Today is {self.current_date} in Pacific Standard Time.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        
        # If chat completions are disabled, use the completions endpoint
        else:
            response = self.openai_client.completions.create(
                model=self.openai_model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                prompt=prompt,
            )
            return response.choices[0].text


    def call_fresheval(self, prefix, question, response, correct_answers, evaluation):
        """
        Call the FreshEval API to evaluate responses.
        """

        # Set the parameters for the OpenAI API
        temperature = 0.0
        max_tokens = 256
        chat_completions = True

        # Generate prompts for demo examples
        demo_prompts = []
        for q, e in zip(self.demo_questions, self.demo_evaluations):
            demo_prompts.append(f"\n\n\nquestion: {q}{e}")

        # Generate the fresh evaluation prompt
        fresheval_demo = "".join(demo_prompts).strip()
        fresheval_question = f"\n\n\nquestion: {question}{evaluation}"

        # Call the OpenAI API to generate responses
        fresh_eval = prefix + "\n\n\n" + fresheval_demo + fresheval_question
        answer = self.call_openai_api(fresh_eval, temperature, max_tokens, chat_completions)

        return answer

    def extract_ratings(self, response):
        """
        Extract the rating from the evaluation response.
        """

        # If the eval answer contains either of these three words, considered as 0
        # including incorrect, not correct, not credited
        pattern = re.compile(
            r"\b(?:incorrect|not\s+correct|not\s+credited)\b", re.IGNORECASE
        )
        if pattern.search(response):
            return 0
        else:
            return 1
        
    def freshqa_piechart(self, result, fig_path: str = "", save: bool = False):
        """
        Plot a pie chart of the true and false answers on FreshQA.

        Parameters
        ----------
        result : dict
            The evaluation result.
        fig_path : str
            The path to save the figure.
        save : bool, optional
            Whether to save the figure, by default True.
        """

        # Given numbers
        sizes = [result["accuracy"], 1 - result["accuracy"]]
        labels = ["True Answer", "False Answer"]
        colors = [(0, 1, 0, 0.5), (1, 0, 0, 0.5)]  # Red and green with 50% transparency

        # Create a new figure
        fig, ax = plt.subplots()

        # Plot pie chart
        plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=140)
        plt.title("Performance on FreshQA Dataset")

        # Equal aspect ratio ensures that pie is drawn as a circle
        plt.axis("equal")

        if save:
            # Save the figure
            plt.tight_layout()
            plt.savefig(os.path.join(fig_path, "freshqa_piechart.pdf"), format="pdf")
            plt.savefig(os.path.join(fig_path, "freshqa_piechart.png"), format="png")

        # Return the figure
        return fig     


    def evaluate_freshqa(self, llm_responses):
        """
        Evaluate the responses generated by the LLM on FreshQA questions.
        """
        
        llm_responses = pd.DataFrame(llm_responses)
        raw_evals = []
        preds = []
        for idx, row in llm_responses.iterrows():
            evaluation = self.evaluation_template.format(
                correct_answers=row["reference_answer"],
                response=row["response"],
            )

            fresheval = self.call_fresheval(
                self.prefix,
                row["question"],
                row["response"],
                row["reference_answer"],
                evaluation,
            )

            evaluation_rating = self.extract_ratings(fresheval)
            raw_evals.append(evaluation)
            preds.append(evaluation_rating)

        # Compute the accuracy (percentage of correct evaluations)
        accuracy = sum(preds) / len(preds)
        result = { "accuracy": accuracy }
        return result, raw_evals, preds

