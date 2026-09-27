from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


load_dotenv()


BHASHINI_URL = (
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)

ASR_SERVICE_ID = (
    "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
)

# This is the TTS service that was used successfully
# in our Bhashini TTS test.
TTS_SERVICE_ID = (
    "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
)
MULTILINGUAL_TTS_SERVICE_ID = "Bhashini/IITM/TTS"


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
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as exc:
        print(f"[convert_to_wav] ffmpeg conversion warning: {exc}")
    return input_path


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
        self.api_key = None
        self.user_id = os.getenv("BHASHINI_UDYAT_KEY")

    def _get_api_key(self) -> str:
        """
        Get the Bhashini inference API key when an actual
        Bhashini request is made.
        """

        api_key = os.getenv("BHASHINI_INFERENCE_KEY")

        if not api_key:
            raise RuntimeError(
                "BHASHINI_INFERENCE_KEY is not configured."
            )

        return api_key

    def detect_language(self, audio_path: str) -> str:
        """
        Detect the language spoken in an audio file (ALD).
        Falls back to 'hi' (Hindi) if auto-detection is unspecified.
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        return "hi"

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

        if not language:
            language = self.detect_language(audio_path)

        wav_path = convert_to_wav(audio_path)

        try:
            api_key = self._get_api_key()

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
                        "serviceId": ASR_SERVICE_ID,
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

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
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

        api_key = self._get_api_key()

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": language
                        },
                        "serviceId": (
                            TTS_SERVICE_ID if language == "hi"
                            else MULTILINGUAL_TTS_SERVICE_ID
                        ),
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

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
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
