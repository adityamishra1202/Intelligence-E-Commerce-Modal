from openai import OpenAI
from django.conf import settings


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

        if self.provider == "ollama":
            self.client = OpenAI(
                base_url=settings.OLLAMA_BASE_URL,
                api_key="ollama",
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=settings.LLM_MAX_RETRIES,
            )
            self.model = settings.OLLAMA_MODEL

        elif self.provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is missing. Check your .env file."
                )

            if not settings.GROQ_MODEL:
                raise ValueError(
                    "GROQ_MODEL is missing. Check your .env file."
                )

            self.client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                timeout=settings.LLM_TIMEOUT_SECONDS,
                max_retries=settings.LLM_MAX_RETRIES,
            )
            self.model = settings.GROQ_MODEL

        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}"
            )

    def generate_response(self, user_message):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EcommerceAI, an intelligent "
                        "e-commerce shopping assistant. "
                        "Help users understand their shopping needs "
                        "and communicate clearly. "
                        "Never invent product prices, availability, "
                        "ratings, or specifications. "
                        "Use verified product data for "
                        "product-specific recommendations."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content