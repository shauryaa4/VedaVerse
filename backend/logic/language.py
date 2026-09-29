from __future__ import annotations

import re
from pathlib import Path

from dotenv import load_dotenv
from backend.logic.bhashini_client import BhashiniError, compute as bhashini_compute

from backend.logic.languages import (
    UnsupportedLanguageError,
    normalize_language_code,
)


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class TranslationError(RuntimeError):
    """Raised when Bhashini translation cannot be completed."""

    pass


def _validate_language(language: str) -> str:
    """
    Validate and normalize a supported language code.

    Examples:
        hi     -> hi
        hi-IN  -> hi
        en_US  -> en

    Unsupported languages raise UnsupportedLanguageError.
    """

    return normalize_language_code(language)


def detect_text_language(text: str) -> str:
    """
    Detect the language of text using Unicode script ranges.

    This is a lightweight script detector, not a legal or
    semantic classifier.

    When no supported Indian-language script is detected,
    English is returned as the default.
    """

    if not text or not text.strip():
        return "en"

    counts = {
        "hi": 0,
        "bn": 0,
        "pa": 0,
        "gu": 0,
        "or": 0,
        "ta": 0,
        "te": 0,
        "kn": 0,
        "ml": 0,
        "ur": 0,
    }

    for char in text:
        cp = ord(char)

        if 0x0900 <= cp <= 0x097F:
            counts["hi"] += 1

        elif 0x0980 <= cp <= 0x09FF:
            counts["bn"] += 1

        elif 0x0A00 <= cp <= 0x0A7F:
            counts["pa"] += 1

        elif 0x0A80 <= cp <= 0x0AFF:
            counts["gu"] += 1

        elif 0x0B00 <= cp <= 0x0B7F:
            counts["or"] += 1

        elif 0x0B80 <= cp <= 0x0BFF:
            counts["ta"] += 1

        elif 0x0C00 <= cp <= 0x0C7F:
            counts["te"] += 1

        elif 0x0C80 <= cp <= 0x0CFF:
            counts["kn"] += 1

        elif 0x0D00 <= cp <= 0x0D7F:
            counts["ml"] += 1

        elif 0x0600 <= cp <= 0x06FF:
            counts["ur"] += 1

    best_lang, best_count = max(
        counts.items(),
        key=lambda item: item[1],
    )

    if best_count > 0:
        return best_lang

    return "en"


def _translate(
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    """
    Perform one Bhashini translation request.

    This function is responsible only for language
    translation. It does not perform classification,
    legal reasoning, routing, retrieval, or decision making.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text cannot be empty.")

    try:
        source_language = _validate_language(source_language)
        target_language = _validate_language(target_language)
    except UnsupportedLanguageError:
        raise

    # No API call is required when source and target are identical.
    if source_language == target_language:
        return text

    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_language,
                        "targetLanguage": target_language,
                    },
                },
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": text,
                }
            ]
        },
    }

    try:
        data = bhashini_compute(
            payload,
            task_type="translation",
            source_language=source_language,
            target_language=target_language,
        )
    except BhashiniError as exc:
        raise TranslationError(str(exc)) from exc

    pipeline_response = data.get("pipelineResponse", [])

    if not pipeline_response:
        raise TranslationError(
            "Bhashini translation returned no pipeline response."
        )

    output = pipeline_response[0].get("output")

    if not output:
        raise TranslationError(
            "Bhashini translation returned no output."
        )

    translated = output[0].get("target")

    if not translated:
        raise TranslationError(
            "Bhashini translation returned no translated text."
        )

    return translated.strip()


def translate_to_english(
    text: str,
    source_language: str,
) -> str:
    """
    Translate user input into English before it enters
    classification, routing, retrieval, or RAG.

    English input is returned unchanged.
    """

    source_language = _validate_language(source_language)

    return _translate(
        text=text,
        source_language=source_language,
        target_language="en",
    )


def translate_from_english(
    text: str,
    target_language: str,
) -> str:
    """
    Translate the final verified English answer into
    the user's selected language.

    Citation markers are protected from translation.
    """

    target_language = _validate_language(target_language)

    if target_language == "en":
        return text

    protected_text, replacements = _protect_citations(text)

    translated = _translate(
        text=protected_text,
        source_language="en",
        target_language=target_language,
    )

    return _restore_citations(
        translated,
        replacements,
    )


# ------------------------------------------------------------------
# Citation protection
# ------------------------------------------------------------------

_CITATION_PATTERN = re.compile(
    r"\[[^\[\]]+:[^\[\]]+\]"
)


def _protect_citations(
    text: str,
) -> tuple[str, dict[str, str]]:
    """
    Replace citation markers such as [IN-1:s3] with
    placeholders before translation.
    """

    citations = _CITATION_PATTERN.findall(text)

    protected = text
    replacements: dict[str, str] = {}

    for index, citation in enumerate(citations):
        placeholder = f"__CITATION_{index}__"

        replacements[placeholder] = citation

        protected = protected.replace(
            citation,
            placeholder,
            1,
        )

    return protected, replacements


def _restore_citations(
    text: str,
    replacements: dict[str, str],
) -> str:
    """
    Restore the original citation markers exactly.
    """

    restored = text

    for placeholder, citation in replacements.items():
        restored = restored.replace(
            placeholder,
            citation,
        )

    return restored
