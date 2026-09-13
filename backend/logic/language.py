from __future__ import annotations

import os
import re

from google import genai


_GEMINI_MODEL = "gemini-3.6-flash"

_SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
}


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    return genai.Client(api_key=api_key)


def _language_name(language: str) -> str:
    try:
        return _SUPPORTED_LANGUAGES[language.lower()]
    except KeyError:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {', '.join(_SUPPORTED_LANGUAGES)}"
        )


def translate_to_english(text: str, source_language: str) -> str:
    """
    Translate a user question into English before it enters
    classification / routing / retrieval / RAG.

    English input is returned unchanged.
    """

    language = source_language.lower()

    if language == "en":
        return text

    source_name = _language_name(language)

    prompt = f"""
Translate the following user question from {source_name} to English.

Rules:
- Return ONLY the translated question.
- Do not answer the question.
- Preserve legal names, statute names, section numbers,
  product names, ingredient names, and technical terms.
- Do not add explanations.
- Do not change the meaning.

User question:
{text}
"""

    # IMPORTANT: the client is assigned to a local variable before use,
    # not chained directly as _get_client().models.generate_content(...).
    # Chaining it inline gives the freshly-created Client object no strong
    # reference anywhere -- if the SDK's internal .models wrapper only holds
    # a WEAK reference back to its parent client, Python's garbage collector
    # is free to destroy the client mid-request (since nothing else is
    # keeping it alive), closing its underlying HTTP transport while the
    # network call is still in flight. This was a live, reproducible bug:
    # "RuntimeError: Cannot send a request, as the client has been closed."
    client = _get_client()
    response = client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
    )

    translated = (response.text or "").strip()

    if not translated:
        raise RuntimeError("Translation to English returned an empty result")

    return translated


_CITATION_PATTERN = re.compile(r"\[[^\[\]]+:[^\[\]]+\]")


def _protect_citations(text: str) -> tuple[str, dict[str, str]]:
    """
    Replace citation markers such as [IN-1:s3] with placeholders
    before translation so the translation model cannot modify them.
    """

    citations = _CITATION_PATTERN.findall(text)

    protected = text

    replacements: dict[str, str] = {}

    for index, citation in enumerate(citations):
        placeholder = f"__CITATION_{index}__"
        replacements[placeholder] = citation
        protected = protected.replace(citation, placeholder, 1)

    return protected, replacements


def _restore_citations(
    text: str,
    replacements: dict[str, str],
) -> str:
    restored = text

    for placeholder, citation in replacements.items():
        restored = restored.replace(placeholder, citation)

    return restored


def translate_from_english(
    text: str,
    target_language: str,
) -> str:
    """
    Translate the final verified English answer into the user's language.

    Citation markers are protected and restored exactly.
    """

    language = target_language.lower()

    if language == "en":
        return text

    target_name = _language_name(language)

    protected_text, replacements = _protect_citations(text)

    prompt = f"""
Translate the following answer from English to {target_name}.

Rules:
- Translate ONLY the natural-language answer.
- Preserve the exact meaning.
- Do not add legal claims.
- Do not remove information.
- Do not add explanations about the translation.
- Preserve every placeholder exactly as written.
- Place each placeholder in the same logical position.
- NEVER translate, modify, remove, or rename placeholders.

Answer:
{protected_text}
"""

    # See translate_to_english() above for why the client is held in a
    # local variable here rather than chained inline off _get_client().
    client = _get_client()
    response = client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
    )

    translated = (response.text or "").strip()

    if not translated:
        raise RuntimeError("Translation from English returned an empty result")

    return _restore_citations(translated, replacements)