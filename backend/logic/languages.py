"""
Canonical language configuration for VedaVerse.

This module is the single backend source of truth for supported
interaction languages. It loads language capabilities from
config/supported_languages.json.

Language capability configuration must not be interpreted as
legal/business logic.
"""

from __future__ import annotations

import json
from pathlib import Path


class UnsupportedLanguageError(ValueError):
    """Raised when a requested language is not supported."""

    def __init__(self, language: str):
        self.language = language
        super().__init__(f"Unsupported language: {language}")


# Repository root:
# backend/logic/languages.py
#       -> backend/logic
#       -> backend
#       -> repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = REPO_ROOT / "config" / "supported_languages.json"


def _load_config() -> dict:
    """Load the canonical language configuration as UTF-8."""
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


_CONFIG = _load_config()

DEFAULT_LANGUAGE: str = _CONFIG["default"]

TRANSLATION_SERVICE_ID: str = _CONFIG["translation_service_id"]

LANGUAGES: dict[str, dict] = _CONFIG["languages"]

SUPPORTED_LANGUAGE_CODES: frozenset[str] = frozenset(LANGUAGES.keys())


def normalize_language_code(language: str) -> str:
    """
    Normalize a language code.

    Examples:
        hi     -> hi
        hi-IN  -> hi
        en_US  -> en
        EN-us  -> en

    Unsupported languages raise UnsupportedLanguageError.
    """

    if not isinstance(language, str) or not language.strip():
        raise UnsupportedLanguageError(str(language))

    normalized = language.strip().lower().replace("_", "-")

    # Accept BCP-47-style regional variants such as hi-IN.
    base_language = normalized.split("-", 1)[0]

    if base_language not in SUPPORTED_LANGUAGE_CODES:
        raise UnsupportedLanguageError(language)

    return base_language


def is_supported_language(language: str) -> bool:
    """Return True when the language is supported."""
    try:
        normalize_language_code(language)
        return True
    except UnsupportedLanguageError:
        return False


def get_language(language: str) -> dict:
    """
    Return the complete configuration for a supported language.
    """
    code = normalize_language_code(language)
    return LANGUAGES[code]