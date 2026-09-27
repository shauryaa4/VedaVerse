from __future__ import annotations

import base64
import os

import requests
from dotenv import load_dotenv


load_dotenv()


BHASHINI_URL = (
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)

TRANSLATION_SERVICE_ID = "bhashini/iiith/nmt-all"


_SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
    "as": "Assamese",
    "sa": "Sanskrit",
    "mai": "Maithili",
    "kok": "Konkani",
    "doi": "Dogri",
    "mni": "Manipuri",
    "sat": "Santali",
    "ks": "Kashmiri",
    "sd": "Sindhi",
    "ne": "Nepali",
    "brx": "Bodo",
}


def _get_api_key() -> str:
    """
    Load the Bhashini inference API key only when a
    translation request is actually made.
    """

    api_key = os.getenv("BHASHINI_INFERENCE_KEY")

    if not api_key:
        raise RuntimeError(
            "BHASHINI_INFERENCE_KEY is not configured."
        )

    return api_key


def _validate_language(language: str) -> str:
    """
    Validate and normalize a Bhashini language code.
    """

    language = language.lower().strip()

    if language not in _SUPPORTED_LANGUAGES:
        # Fall back to English if an unsupported code is provided
        return "en"

    return language


def detect_text_language(text: str) -> str:
    """
    Detect language of input text using Unicode script ranges (TLD).
    Returns Bhashini language code (e.g. 'hi', 'ta', 'bn', 'te', 'mr', 'gu', 'kn', 'ml', 'en').
    """
    if not text or not text.strip():
        return "en"

    # Count characters in Unicode script ranges
    counts = {
        "hi": 0,  # Devanagari (Hindi / Marathi)
        "bn": 0,  # Bengali / Assamese
        "pa": 0,  # Gurmukhi / Punjabi
        "gu": 0,  # Gujarati
        "or": 0,  # Odia
        "ta": 0,  # Tamil
        "te": 0,  # Telugu
        "kn": 0,  # Kannada
        "ml": 0,  # Malayalam
        "ur": 0,  # Urdu / Arabic script
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

    best_lang, best_count = max(counts.items(), key=lambda x: x[1])
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
    """

    if not text.strip():
        raise ValueError("Text cannot be empty.")

    source_language = _validate_language(source_language)
    target_language = _validate_language(target_language)

    # No API call is needed when source and target are identical.
    if source_language == target_language:
        return text

    api_key = _get_api_key()

    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_language,
                        "targetLanguage": target_language,
                    },
                    "serviceId": TRANSLATION_SERVICE_ID,
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

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "*/*",
    }

    response = requests.post(
        BHASHINI_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    pipeline_response = data.get("pipelineResponse", [])

    if not pipeline_response:
        raise RuntimeError(
            "Bhashini translation returned no pipeline response."
        )

    output = pipeline_response[0].get("output")

    if not output:
        raise RuntimeError(
            "Bhashini translation returned no output."
        )

    translated = output[0].get("target")

    if not translated:
        # Some Bhashini translation responses may expose
        # the translated text under a different field.
        # Keep this explicit rather than silently returning
        # an incorrect value.
        raise RuntimeError(
            f"Bhashini translation returned an unexpected "
            f"response: {data}"
        )

    return translated.strip()


def translate_to_english(
    text: str,
    source_language: str,
) -> str:
    """
    Translate user input into English before it enters
    classification / routing / retrieval / RAG.

    English input is returned unchanged.
    """

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

import re


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