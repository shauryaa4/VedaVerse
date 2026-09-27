from __future__ import annotations

import base64
import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.logic.language import (
    detect_text_language,
    translate_from_english,
    translate_to_english,
)
from backend.logic.speech import speech_service
from backend.routes.query import QueryRequest, query_endpoint

router = APIRouter(prefix="/voice", tags=["Voice"])


class TTSRequest(BaseModel):
    text: str
    language: str = "hi"


@router.post("/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
):
    """
    Convert uploaded speech audio into text via Bhashini ASR.
    """
    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio file is required.",
        )

    suffix = os.path.splitext(audio.filename)[1] or ".wav"

    try:
        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty.",
            )

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            result = speech_service.speech_to_text(
                temp_path,
                language=language,
            )

            detected = result.language or detect_text_language(result.text)

            return {
                "text": result.text,
                "language": detected,
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Speech processing failed: {exc}",
        )


@router.post("/tts")
def text_to_speech_route(req: TTSRequest):
    """
    Convert text to speech audio via Bhashini TTS.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_bytes = speech_service.text_to_speech(req.text, req.language)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "audio_base64": audio_b64,
            "language": req.language,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Text-to-speech generation failed: {exc}",
        )


@router.post("/chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    language: str | None = Form(None),
):
    """
    End-to-End Bhashini Voice Chat Pipeline:
    1. Speech to Text (ASR via Bhashini)
    2. Language Detection (TLD / ALD)
    3. Neural Machine Translation to English (NMT via Bhashini)
    4. Execution of Main PIP-RAG-Confidence Pipeline
    5. Neural Machine Translation back to User Language (NMT via Bhashini)
    6. Text to Speech in User Language (TTS via Bhashini)
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    suffix = os.path.splitext(audio.filename)[1] or ".wav"
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(audio_bytes)
        temp_path = temp_file.name

    try:
        # Step 1: Bhashini ASR
        asr_result = speech_service.speech_to_text(temp_path, language=language)
        user_transcript = asr_result.text

        # Step 2: Language Detection
        detected_lang = (
            language or asr_result.language or detect_text_language(user_transcript)
        )

        # Step 3: NMT to English
        english_question = translate_to_english(user_transcript, detected_lang)

        # Step 4: Run Main PIP-RAG-Confidence Pipeline via query_endpoint
        query_req = QueryRequest(
            session_id=session_id,
            question=user_transcript,
            language=detected_lang,
        )
        rag_res = query_endpoint(query_req)

        # Step 5: Bhashini TTS (Voice answer generation)
        audio_b64 = None
        try:
            if rag_res.answer_text and rag_res.answer_text.strip():
                tts_bytes = speech_service.text_to_speech(
                    rag_res.answer_text, detected_lang
                )
                audio_b64 = base64.b64encode(tts_bytes).decode("utf-8")
        except Exception as tts_err:
            print(f"[voice_chat] TTS fallback warning: {tts_err}")

        return {
            "transcript": user_transcript,
            "detected_language": detected_lang,
            "english_question": english_question,
            "result": rag_res,
            "audio_base64": audio_b64,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)