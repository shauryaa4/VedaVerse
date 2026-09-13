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

    response = _get_client().models.generate_content(
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

    response = _get_client().models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
    )

    translated = (response.text or "").strip()

    if not translated:
        raise RuntimeError("Translation from English returned an empty result")

    return _restore_citations(translated, replacements)