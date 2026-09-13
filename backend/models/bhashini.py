from pydantic import BaseModel


class TranslationResult(BaseModel):
    """
    Result of a mock Bhashini translation call.
    mock is always True in the demo build — there is no live Bhashini
    integration. This field must never be silently dropped downstream.
    """
    original_text: str
    translated_text: str
    source_lang: str   # "hi" | "ta" | "bn" | "en" etc.
    target_lang: str
    matched_known_phrase: bool  # True if we found an exact demo entry
    mock: bool = True
