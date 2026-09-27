from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.language import (
    _translate,
    detect_text_language,
    translate_from_english,
    translate_to_english,
)

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
    except Exception as exc:
        # Fallback to original text if Bhashini call fails
        return TranslationResult(
            original_text=req.text,
            translated_text=req.text,
            source_lang=req.source_lang or "en",
            target_lang=req.lang,
        )


@router.post("/translate_batch")
def bhashini_translate_batch(req: BatchTranslateRequest):
    """
    Translate a list of strings using Bhashini NMT service.
    """
    if req.source_lang == req.target_lang or not req.texts:
        return {"translations": req.texts}

    results = []
    for text in req.texts:
        if not text or not text.strip():
            results.append(text)
            continue
        try:
            trans = _translate(
                text=text,
                source_language=req.source_lang,
                target_language=req.target_lang,
            )
            results.append(trans)
        except Exception:
            results.append(text)

    return {"translations": results}


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
    except Exception:
        return TranslationResult(
            original_text=req.text,
            translated_text=req.text,
            source_lang=req.lang,
            target_lang="en",
        )


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
    except Exception:
        return TranslationResult(
            original_text=req.text,
            translated_text=req.text,
            source_lang="en",
            target_lang=req.lang,
        )
