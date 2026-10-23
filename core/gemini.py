
"""Google Gemini wrapper for CareerCompass AI."""

import os
from pathlib import Path

from dotenv import load_dotenv


# --------------------------------------------------
# Load .env from the project root
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE, override=False)


# --------------------------------------------------
# Configuration
# --------------------------------------------------
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv(
    "GEMINI_EMBED_MODEL",
    "gemini-embedding-001",
)


class GeminiError(Exception):
    """Raised when a Gemini API operation fails."""


def available() -> bool:
    """Return True when a Gemini API key is configured."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(key)


def _client():
    """Create a Gemini client using the configured API key."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY is not configured. "
            "Check the .env file in your project root."
        )

    try:
        from google import genai

        return genai.Client(api_key=api_key)

    except ImportError as error:
        raise GeminiError(
            "The Google Gen AI SDK is not installed. "
            "Run: pip install google-genai"
        ) from error

    except Exception as error:
        raise _friendly(error) from error


def _friendly(error: Exception) -> GeminiError:
    """Convert API errors into readable messages."""
    message = str(error)
    upper_message = message.upper()

    if "429" in message or "RESOURCE_EXHAUSTED" in upper_message:
        return GeminiError(
            "Gemini quota exceeded. Check your Google AI Studio "
            "quota and billing, or try again later."
        )

    if (
        "API KEY" in upper_message
        or "401" in message
        or "403" in message
        or "PERMISSION_DENIED" in upper_message
        or "UNAUTHENTICATED" in upper_message
    ):
        return GeminiError(
            "Gemini rejected the API key. Verify the key in your "
            "project's .env file and check that it is valid."
        )

    if "404" in message or "NOT_FOUND" in upper_message:
        return GeminiError(
            f"Gemini model '{MODEL}' or the requested resource "
            "was not found. Check the configured model name."
        )

    return GeminiError(
        f"Gemini request failed: {message[:300]}"
    )


def generate(prompt: str, system: str | None = None) -> str:
    """Generate a text response using Gemini."""
    client = _client()

    try:
        from google.genai import types

        config = (
            types.GenerateContentConfig(
                system_instruction=system
            )
            if system
            else None
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=config,
        )

        response_text = (response.text or "").strip()

        if not response_text:
            raise GeminiError(
                "Gemini returned an empty response. "
                "The request may have been blocked by safety filters."
            )

        return response_text

    except GeminiError:
        raise

    except Exception as error:
        raise _friendly(error) from error


def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    client = _client()

    try:
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=texts,
        )

        return [
            embedding.values
            for embedding in (response.embeddings or [])
        ]

    except GeminiError:
        raise

    except Exception as error:
        raise _friendly(error) from error


SYSTEM_COACH = (
    "You are CareerCompass AI, a practical, honest career coach "
    "for students and job seekers. Base answers on the user's "
    "profile and provided context. Never invent qualifications, "
    "employers, or credentials the user did not provide. "
    "Be concise and use bullet points."
)
