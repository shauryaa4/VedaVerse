from __future__ import annotations

import base64
import os
import shutil
import wave
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from backend.logic.languages import normalize_language_code
from backend.logic.bhashini_client import BhashiniError, compute as bhashini_compute


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass
class SpeechResult:
    """
    Result returned after processing speech input.
    """

    text: str
    language: str


import subprocess


def convert_to_wav(input_path: str) -> str:
    """
    Convert browser-recorded audio (WebM, Ogg, MP4, AAC) to standard 16kHz mono WAV using ffmpeg.
    """
    output_path = input_path + "_converted.wav"
    try:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                ffmpeg = "ffmpeg"
        subprocess.run(
            [ffmpeg, "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as exc:
        try:
            with wave.open(input_path, "rb") as wav_file:
                compatible = (
                    wav_file.getnchannels() == 1
                    and wav_file.getsampwidth() == 2
                    and wav_file.getframerate() == 16000
                )
        except (wave.Error, OSError):
            compatible = False
        if compatible:
            return input_path
        raise RuntimeError(
            "Audio conversion failed. Install the backend requirements (including "
            "imageio-ffmpeg), install ffmpeg on the backend host, "
            "or upload 16 kHz mono PCM WAV audio."
        ) from exc
    raise RuntimeError("Audio conversion produced no usable WAV file.")


class BhashiniSpeechService:
    """
    Bhashini-based speech service.

    Handles:
    - Audio language detection
    - Speech-to-text (ASR)
    - Text-to-speech (TTS)

    Credentials are checked inside the actual API methods,
    so importing this service does not prevent FastAPI
    from starting when the Bhashini API key is missing.
    """

    def __init__(self) -> None:
        """Credentials are read lazily so importing the service is safe."""

    def _compute(
        self,
        payload: dict,
        task_type: str,
        source_language: str = "",
        target_language: str = "",
    ) -> dict:
        try:
            return bhashini_compute(
                payload,
                task_type=task_type,
                source_language=source_language,
                target_language=target_language,
            )
        except BhashiniError as exc:
            raise RuntimeError(str(exc)) from exc

    def _detect_language_from_wav(self, wav_path: str) -> str:
        with open(wav_path, "rb") as audio_file:
            audio_content = base64.b64encode(audio_file.read()).decode("utf-8")
        data = self._compute({
            "pipelineTasks": [{
                "taskType": "audio-lang-detection",
                "config": {},
            }],
            "inputData": {"audio": [{"audioContent": audio_content}]},
        }, task_type="audio-lang-detection")
        try:
            detected = data["pipelineResponse"][0]["output"][0]["langPrediction"][0]["langCode"]
            return normalize_language_code(detected)
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Bhashini audio language detection returned no language.") from exc

    def detect_language(self, audio_path: str) -> str:
        """
        Detect the language spoken in an audio file with Bhashini ALD.
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        wav_path = convert_to_wav(audio_path)
        try:
            return self._detect_language_from_wav(wav_path)
        finally:
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)

    def speech_to_text(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> SpeechResult:
        """
        Convert speech audio into text using Bhashini ASR.

        Args:
            audio_path: Path to a audio file.
            language: Bhashini language code such as 'hi'.

        Returns:
            SpeechResult containing transcript and language.
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        wav_path = convert_to_wav(audio_path)
        try:
            if not language:
                language = self._detect_language_from_wav(wav_path)
            language = normalize_language_code(language)
            with open(wav_path, "rb") as audio_file:
                audio_content = base64.b64encode(
                    audio_file.read()
                ).decode("utf-8")
        finally:
            if wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass


        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": language
                        },
                        "audioFormat": "wav",
                        "samplingRate": 16000,
                    },
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": audio_content
                    }
                ]
            },
        }

        data = self._compute(payload, task_type="asr", source_language=language)

        pipeline_response = data.get("pipelineResponse", [])

        if not pipeline_response:
            raise RuntimeError(
                "Bhashini ASR returned no pipeline response."
            )

        output = pipeline_response[0].get("output")

        if not output:
            raise RuntimeError(
                "Bhashini ASR returned no transcript."
            )

        transcript = output[0].get("source")

        if not transcript:
            raise RuntimeError(
                "Bhashini ASR response did not contain transcript text."
            )

        return SpeechResult(
            text=transcript,
            language=language,
        )

    def text_to_speech(
        self,
        text: str,
        language: str,
    ) -> bytes:
        """
        Convert text into spoken audio using Bhashini TTS.

        Args:
            text: Text that should be spoken.
            language: Target language code.

        Returns:
            Decoded audio bytes.
        """

        if not text.strip():
            raise ValueError("Text cannot be empty.")

        if not language.strip():
            raise ValueError("Language cannot be empty.")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": language
                        },
                        "gender": "female",
                    },
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            },
        }

        language = normalize_language_code(language)
        data = self._compute(payload, task_type="tts", source_language=language)

        pipeline_response = data.get("pipelineResponse", [])

        if not pipeline_response:
            raise RuntimeError(
                "Bhashini TTS returned no pipeline response."
            )

        audio = pipeline_response[0].get("audio", [])

        if not audio:
            raise RuntimeError(
                "Bhashini TTS returned no audio."
            )

        audio_content = audio[0].get("audioContent")

        if not audio_content:
            raise RuntimeError(
                "Bhashini TTS response did not contain audioContent."
            )

        return base64.b64decode(audio_content)


# Shared service instance
speech_service = BhashiniSpeechService()
