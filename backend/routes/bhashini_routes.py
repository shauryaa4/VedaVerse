from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.language import (
    TranslationError,
    _translate,
    detect_text_language,
    transliterate_from_english,
    translate_from_english,
    translate_many_from_english,
    translate_to_english,
    transliterate_many_from_english,
)
from backend.logic.languages import UnsupportedLanguageError

router = APIRouter(prefix="/bhashini", tags=["Bhashini Translation"])


class TranslateRequest(BaseModel):
    text: str
    lang: str = "en"  # "hi" | "ta" | "bn" | "te" | "mr" | "gu" | "kn" | "ml" | "en" etc.
    source_lang: str | None = None


class BatchTranslateRequest(BaseModel):
    texts: list[str]
    target_lang: str = "hi"
    source_lang: str = "en"


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


def _raise_translation_error(exc: Exception) -> None:
    if isinstance(exc, UnsupportedLanguageError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if isinstance(exc, TranslationError):
        raise HTTPException(
            status_code=502,
            detail={"code": "BHASHINI_TRANSLATION_FAILED", "message": str(exc)},
        ) from exc
    raise exc


@router.post("/translate", response_model=TranslationResult)
def bhashini_translate(req: TranslateRequest):
    """
    Translate arbitrary text using Bhashini NMT service.
    """
    if not req.text or not req.text.strip():
        return TranslationResult(
            original_text=req.text,
            translated_text=req.text,
            source_lang=req.source_lang or "en",
            target_lang=req.lang,
        )

    try:
        source_lang = req.source_lang or detect_text_language(req.text)
        translated = _translate(
            text=req.text,
            source_language=source_lang,
            target_language=req.lang,
        )
        return TranslationResult(
            original_text=req.text,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=req.lang,
        )
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)


@router.post("/transliterate", response_model=TranslationResult)
def bhashini_transliterate(req: TranslateRequest):
    """Phonetically render English UI text in an Indian-language script."""
    try:
        source_lang = req.source_lang or "en"
        if source_lang != "en":
            raise UnsupportedLanguageError(source_lang)
        transliterated = transliterate_from_english(req.text, req.lang)
        return TranslationResult(
            original_text=req.text,
            translated_text=transliterated,
            source_lang="en",
            target_lang=req.lang,
        )
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)


@router.post("/translate_batch")
def bhashini_translate_batch(req: BatchTranslateRequest):
    """
    Translate a list of strings using Bhashini NMT service.
    """
    if req.source_lang == req.target_lang or not req.texts:
        return {"translations": req.texts}

    try:
        # Keep requests small enough for Bhashini while avoiding one network
        # round trip per UI text fragment. Empty strings stay in their slots.
        results = list(req.texts)
        for start in range(0, len(req.texts), 10):
            chunk = req.texts[start : start + 10]
            indexes = [i for i, text in enumerate(chunk) if text and text.strip()]
            if not indexes:
                continue
            translated = translate_many_from_english(
                [chunk[i] for i in indexes], req.target_lang, req.source_lang
            )
            for i, value in zip(indexes, translated):
                results[start + i] = value
        return {"translations": results}
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)


@router.post("/transliterate_batch")
def bhashini_transliterate_batch(req: BatchTranslateRequest):
    """Phonetically render a group of English technical terms into one script."""
    if req.source_lang != "en":
        raise HTTPException(status_code=422, detail="Transliteration source language must be en.")
    if req.target_lang == "en" or not req.texts:
        return {"translations": req.texts}
    try:
        results = list(req.texts)
        for start in range(0, len(req.texts), 10):
            chunk = req.texts[start : start + 10]
            indexes = [i for i, text in enumerate(chunk) if text and text.strip()]
            if not indexes:
                continue
            rendered = transliterate_many_from_english(
                [chunk[i] for i in indexes], req.target_lang
            )
            for i, value in zip(indexes, rendered):
                results[start + i] = value
        return {"translations": results}
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)


@router.post("/in", response_model=TranslationResult)
def bhashini_translate_in(req: TranslateRequest):
    """
    Translate user input into English via Bhashini NMT.
    """
    try:
        translated = translate_to_english(req.text, req.lang)
        return TranslationResult(
            original_text=req.text,
            translated_text=translated,
            source_lang=req.lang,
            target_lang="en",
        )
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)


@router.post("/out", response_model=TranslationResult)
def bhashini_translate_out(req: TranslateRequest):
    """
    Translate English answer into target language via Bhashini NMT.
    """
    try:
        translated = translate_from_english(req.text, req.lang)
        return TranslationResult(
            original_text=req.text,
            translated_text=translated,
            source_lang="en",
            target_lang=req.lang,
        )
    except (TranslationError, UnsupportedLanguageError) as exc:
        _raise_translation_error(exc)
