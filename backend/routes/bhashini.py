from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.bhashini_mock import translate_in, translate_out
from backend.models.bhashini import TranslationResult

router = APIRouter(prefix="/bhashini", tags=["bhashini"])


class TranslateRequest(BaseModel):
    text: str
    lang: str  # "hi" | "ta" | "bn" | "en" etc.


@router.post("/in", response_model=TranslationResult)
def bhashini_translate_in(req: TranslateRequest):
    return translate_in(req.text, req.lang)


@router.post("/out", response_model=TranslationResult)
def bhashini_translate_out(req: TranslateRequest):
    return translate_out(req.text, req.lang)
