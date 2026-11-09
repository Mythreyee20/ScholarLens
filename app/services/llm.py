
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq

from app.config import get_settings


load_dotenv()


class LLMService:

    # Set LLM_PROVIDER=groq for faster evaluation.
    # Set LLM_PROVIDER=auto to use Gemini first, then Groq.
    PROVIDER_MODE = os.getenv("LLM_PROVIDER", "groq").lower()

    usage = {
        "total_requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "last_provider": None,
        "last_model": None,
    }

    def __init__(self):
        settings = get_settings()

        self.gemini = None

        if self.PROVIDER_MODE != "groq":
            self.gemini = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=30000),
            )

        self.groq = Groq(
            api_key=settings.groq_api_key,
            timeout=30.0,
            max_retries=2,
        )

    @classmethod
    def record_usage(
        cls,
        provider,
        model,
        input_tokens,
        output_tokens,
        input_rate,
        output_rate,
    ):
        cost = (
            input_tokens * input_rate
            + output_tokens * output_rate
        ) / 1_000_000

        cls.usage["total_requests"] += 1
        cls.usage["input_tokens"] += input_tokens
        cls.usage["output_tokens"] += output_tokens
        cls.usage["total_tokens"] += input_tokens + output_tokens
        cls.usage["estimated_cost_usd"] += cost
        cls.usage["last_provider"] = provider
        cls.usage["last_model"] = model

    @classmethod
    def get_usage(cls):
        return cls.usage.copy()

    def generate(self, prompt: str) -> str:

        # Gemini primary provider (only in auto mode)
        if self.gemini is not None:
            try:
                response = self.gemini.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )

                if response.text:
                    metadata = response.usage_metadata

                    input_tokens = metadata.prompt_token_count or 0
                    output_tokens = metadata.candidates_token_count or 0

                    self.record_usage(
                        "Gemini",
                        "gemini-3.8-flash",
                        input_tokens,
                        output_tokens,
                        0.75,
                        3.75,
                    )

                    return response.text

            except Exception as error:
                print(f"Gemini failed: {error}")

        # Groq provider
        try:
            response = self.groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

            self.record_usage(
                "Groq",
                "openai/gpt-oss-120b",
                input_tokens,
                output_tokens,
                0.15,
                0.60,
            )

            return response.choices[0].message.content or ""

        except Exception as error:
            print(f"Groq failed: {error}")
            raise RuntimeError(
                "LLM generation failed."
            ) from error

    def stream_generate(self, prompt: str):

        # Gemini streaming (only in auto mode)
        if self.gemini is not None:
            generated_text = False

            try:
                input_tokens = 0
                output_tokens = 0

                stream = self.gemini.models.generate_content_stream(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )

                for chunk in stream:
                    if chunk.text:
                        generated_text = True
                        yield chunk.text

                    metadata = chunk.usage_metadata

                    if metadata:
                        input_tokens = (
                            metadata.prompt_token_count or input_tokens
                        )
                        output_tokens = (
                            metadata.candidates_token_count or output_tokens
                        )

                self.record_usage(
                    "Gemini",
                    "gemini-3.8-flash",
                    input_tokens,
                    output_tokens,
                    0.75,
                    3.75,
                )

                return

            except Exception as error:
                print(f"Gemini streaming failed: {error}")

                if generated_text:
                    raise RuntimeError(
                        "Gemini streaming failed after partial output."
                    ) from error

        # Groq streaming
        try:
            input_tokens = 0
            output_tokens = 0

            stream = self.groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in stream:
                if chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens or 0
                    output_tokens = chunk.usage.completion_tokens or 0

                if chunk.choices:
                    content = chunk.choices[0].delta.content

                    if content:
                        yield content

            self.record_usage(
                "Groq",
                "openai/gpt-oss-120b",
                input_tokens,
                output_tokens,
                0.15,
                0.60,
            )

        except Exception as error:
            print(f"Groq streaming failed: {error}")
            raise RuntimeError(
                "Groq generation failed."
            ) from error
