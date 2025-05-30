from __future__ import annotations

import os
import json
import ast
import openai
import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT


class OpenAIChat:
    def __init__(
        self,
        model_name,
        max_tokens=2500,
        temperature=0,
        top_p=1,
        request_timeout=20,
    ):
        if "gpt" not in model_name:
            openai.api_base = "http://localhost:8000/v1"
        else:
            # openai.api_base = "https://api.openai.com/v1"
            openai.api_key = os.environ.get("OPENAI_API_KEY", None)
            assert (
                openai.api_key is not None
            ), "Please set the OPENAI_API_KEY environment variable."
            assert (
                openai.api_key != ""
            ), "Please set the OPENAI_API_KEY environment variable."
        self.client = AsyncOpenAI()

        self.config = {
            "model_name": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "request_timeout": request_timeout,
        }

    def extract_list_from_string(self, input_string):
        start_index = input_string.find("[")
        end_index = input_string.rfind("]")

        if start_index != -1 and end_index != -1 and start_index < end_index:
            return input_string[start_index : end_index + 1]
        else:
            return None

    def extract_dict_from_string(self, input_string):
        start_index = input_string.find("{")
        end_index = input_string.rfind("}")

        if start_index != -1 and end_index != -1 and start_index < end_index:
            return input_string[start_index : end_index + 1]
        else:
            return None

    def _json_fix(self, output):
        return output.replace("```json\n", "").replace("\n```", "")

    def _boolean_fix(self, output):
        return output.replace("true", "True").replace("false", "False")

    def _type_check(self, output, expected_type):
        try:
            output_eval = ast.literal_eval(output)
            if not isinstance(output_eval, expected_type):
                print(
                    f"Type mismatch: expected {expected_type}, got {type(output_eval)}"
                )
                return None
            return output_eval
        except:
            if expected_type == str:
                return output
            else:
                print(f"Error evaluating output: {output}")
                return None

    async def dispatch_openai_requests(
        self,
        messages_list,
    ) -> list[str]:
        """Dispatches requests to OpenAI API asynchronously.

        Args:
            messages_list: List of messages to be sent to OpenAI ChatCompletion API.
        Returns:
            List of responses from OpenAI API.
        """

        async def _request_with_retry(messages, retry=3):
            for _ in range(retry):
                try:
                    response = await asyncio.wait_for(
                        self.client.chat.completions.create(
                            model=self.config["model_name"],
                            messages=messages,
                            max_tokens=self.config["max_tokens"],
                            temperature=self.config["temperature"],
                            top_p=self.config["top_p"],
                        ),
                        timeout=self.config["request_timeout"],  # seconds
                    )
                    return response
                except asyncio.TimeoutError:
                    print("Timeout reached for request. Retrying...")
                    await asyncio.sleep(1)
                except openai.RateLimitError:
                    await asyncio.sleep(1)
                except openai.Timeout:
                    await asyncio.sleep(1)
                except openai.APIError:
                    await asyncio.sleep(1)
            return None

        async_responses = [_request_with_retry(messages) for messages in messages_list]

        return await asyncio.gather(*async_responses, return_exceptions=True)

    def run(self, messages_list, expected_type):
        retry = 1
        responses = [None for _ in range(len(messages_list))]
        messages_list_cur_index = [i for i in range(len(messages_list))]

        while retry > 0 and len(messages_list_cur_index) > 0:
            messages_list_cur = [messages_list[i] for i in messages_list_cur_index]

            predictions = asyncio.run(
                self.dispatch_openai_requests(
                    messages_list=messages_list_cur,
                )
            )

            # Save the cost of the API call to a JSONL file
            if os.environ.get("SAVE_MODEL_COST", "False") == "True":
                MODEL_COST_PATH = os.environ.get("MODEL_COST_PATH", "model_cost.jsonl")
                for prediction in predictions:
                    if prediction is not None:
                        if hasattr(prediction, "usage"):
                            completion_tokens = prediction.usage.completion_tokens
                            prompt_tokens = prediction.usage.prompt_tokens
                            total_tokens = prediction.usage.total_tokens
                            with open(MODEL_COST_PATH, "a") as f:
                                f.write(
                                    json.dumps(
                                        {
                                            "model": self.config["model_name"],
                                            "prompt_tokens": prompt_tokens,
                                            "completion_tokens": completion_tokens,
                                            "total_tokens": total_tokens,
                                        }
                                    )
                                    + "\n"
                                )

            preds = [
                self._type_check(
                    self._boolean_fix(
                        self._json_fix(prediction.choices[0].message.content)
                    ),
                    expected_type,
                )
                if prediction is not None and hasattr(prediction, "choices")
                else None
                for prediction in predictions
            ]
            finised_index = []
            for i, pred in enumerate(preds):
                if pred is not None:
                    responses[messages_list_cur_index[i]] = pred
                    finised_index.append(messages_list_cur_index[i])

            messages_list_cur_index = [
                i for i in messages_list_cur_index if i not in finised_index
            ]

            retry -= 1

        return responses


class AnthropicChat:
    def __init__(
        self,
        model_name: str,
        max_tokens: int = 2500,
        temperature: float = 0,
        top_p: float = 1,
        request_timeout: float = 20,
    ):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        assert api_key, "Please set the ANTHROPIC_API_KEY environment variable."

        self.client = AsyncAnthropic(api_key=api_key)
        self.config = {
            "model_name": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "request_timeout": request_timeout,
        }

    def extract_list_from_string(self, input_string: str) -> str | None:
        start = input_string.find("[")
        end = input_string.rfind("]")
        if start != -1 and end != -1 and start < end:
            return input_string[start : end + 1]
        return None

    def extract_dict_from_string(self, input_string: str) -> str | None:
        start = input_string.find("{")
        end = input_string.rfind("}")
        if start != -1 and end != -1 and start < end:
            return input_string[start : end + 1]
        return None

    def _json_fix(self, output: str) -> str:
        if isinstance(output, str):
            return output.replace("```json\n", "").replace("\n```", "")
        else:
            return output

    def _boolean_fix(self, output: str) -> str:
        if isinstance(output, str):
            return output.replace("true", "True").replace("false", "False")
        else:
            return output

    def _type_check(self, output: str, expected_type: type):
        try:
            val = ast.literal_eval(output)
            if not isinstance(val, expected_type):
                print(f"Type mismatch: expected {expected_type}, got {type(val)}")
                return None
            return val
        except Exception:
            if expected_type == str:
                return output
            print(f"Error evaluating output: {output}")
            return None

    async def dispatch_anthropic_requests(
        self,
        messages_list: list[list[dict]],
    ) -> list[object | None]:
        """Send batches via the Messages API with retries."""

        async def _request_with_retry(
            messages: list[dict], retry: int = 3
        ) -> object | None:
            # Extract any system prompt to top‐level
            system_content = None
            filtered = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_content = msg["content"]
                else:
                    filtered.append({"role": msg["role"], "content": msg["content"]})

            for _ in range(retry):
                try:
                    return await asyncio.wait_for(
                        self.client.messages.create(
                            model=self.config["model_name"],
                            system=system_content,
                            messages=filtered,
                            max_tokens=self.config["max_tokens"],
                            temperature=self.config["temperature"],
                            top_p=self.config["top_p"],
                        ),
                        timeout=self.config["request_timeout"],
                    )
                except asyncio.TimeoutError:
                    print("Anthropic request timed out, retrying…")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Anthropic API error ({e}), retrying…")
                    await asyncio.sleep(1)
            return None

        tasks = [_request_with_retry(msgs) for msgs in messages_list]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def run(
        self,
        messages_list: list[list[dict]],
        expected_type: type,
    ) -> list[object | None]:
        """Dispatch messages and type‐check their responses."""
        responses = [None] * len(messages_list)
        pending_idx = list(range(len(messages_list)))
        attempts = 1

        while attempts > 0 and pending_idx:
            batch = [messages_list[i] for i in pending_idx]
            completions = asyncio.run(self.dispatch_anthropic_requests(batch))
            finished = []

            for idx_in_batch, comp in enumerate(completions):
                if comp is None or not hasattr(comp, "content"):
                    continue

                raw = comp.content
                # Optional cost logging
                if os.environ.get("SAVE_MODEL_COST", "False") == "True" and hasattr(
                    comp, "usage"
                ):
                    MODEL_COST_PATH = os.environ.get(
                        "MODEL_COST_PATH", "model_cost.jsonl"
                    )
                    with open(MODEL_COST_PATH, "a") as f:
                        f.write(
                            json.dumps(
                                {
                                    "model": self.config["model_name"],
                                    "input_tokens": comp.usage.input_tokens,
                                    "output_tokens": comp.usage.output_tokens,
                                    "total_tokens": comp.usage.input_tokens
                                    + comp.usage.output_tokens,
                                }
                            )
                            + "\n"
                        )

                # Parse TextBox list
                raw_text = ""
                for i in range(len(raw)):
                    raw_text += raw[i].text

                cleaned = self._boolean_fix(self._json_fix(raw_text))
                result = self._type_check(cleaned, expected_type)
                if result is not None:
                    real_idx = pending_idx[idx_in_batch]
                    responses[real_idx] = result
                    finished.append(real_idx)

            pending_idx = [i for i in pending_idx if i not in finished]
            attempts -= 1

        return responses
