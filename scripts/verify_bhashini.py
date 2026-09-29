"""
Verify the configured Bhashini translation pipeline.

Usage:
    python scripts/verify_bhashini.py

This script:
- Loads .env from the repository root.
- Checks BHASHINI_UDYAT_KEY and BHASHINI_INFERENCE_KEY are present.
- Reads the canonical language configuration.
- Probes the configured Bhashini translation service for each
  configured non-English language.
- Never prints credential values.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "supported_languages.json"

load_dotenv(REPO_ROOT / ".env")


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

BHASHINI_ENDPOINT = (
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Language configuration not found: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def probe_translation(
    inference_key: str,
    service_id: str,
    source_language: str,
    target_language: str,
) -> tuple[bool, str]:
    """
    Send a minimal translation request to the configured
    Bhashini Dhruva pipeline.
    """

    headers = {
        "Authorization": inference_key,
        "Content-Type": "application/json",
    }

    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": source_language,
                        "targetLanguage": target_language,
                    },
                    "serviceId": service_id,
                },
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": "Hello, this is a Bhashini verification test."
                }
            ]
        },
    }

    try:
        response = requests.post(
            BHASHINI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30,
        )
    except requests.Timeout:
        return False, "TIMEOUT"
    except requests.RequestException as exc:
        return False, f"NETWORK_ERROR: {type(exc).__name__}"

    if response.status_code != 200:
        return False, f"HTTP_{response.status_code}"

    try:
        data = response.json()
    except ValueError:
        return False, "INVALID_JSON"

    pipeline_response = data.get("pipelineResponse")

    if not pipeline_response:
        return False, "EMPTY_PIPELINE_RESPONSE"

    # Look for an actual translation output.
    for task in pipeline_response:
        output = task.get("output")

        if output:
            for item in output:
                translated = item.get("target")

                if translated:
                    return True, "OK"

    return False, "EMPTY_TRANSLATION_OUTPUT"


# ---------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("VedaVerse — Bhashini Verification")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Check credentials
    # ---------------------------------------------------------------

    udyat_key = os.getenv("BHASHINI_UDYAT_KEY")
    inference_key = os.getenv("BHASHINI_INFERENCE_KEY")

    print("\n[1] Credential check")

    print(
        "BHASHINI_UDYAT_KEY present:",
        bool(udyat_key),
    )

    print(
        "BHASHINI_INFERENCE_KEY present:",
        bool(inference_key),
    )

    if not inference_key:
        print(
            "\nRESULT: BLOCKED — "
            "BHASHINI_INFERENCE_KEY is missing from .env"
        )
        return 1

    # UDYAT is recorded separately because the current implementation
    # uses the inference key for Dhruva translation calls.
    if not udyat_key:
        print(
            "WARNING: BHASHINI_UDYAT_KEY is missing. "
            "Translation verification can still proceed using "
            "BHASHINI_INFERENCE_KEY."
        )

    # ---------------------------------------------------------------
    # 2. Load language configuration
    # ---------------------------------------------------------------

    print("\n[2] Loading canonical language configuration")

    try:
        config = load_config()
    except Exception as exc:
        print(f"RESULT: BLOCKED — {exc}")
        return 1

    service_id = config.get("translation_service_id")

    if not service_id:
        print(
            "RESULT: BLOCKED — "
            "translation_service_id is missing from "
            "config/supported_languages.json"
        )
        return 1

    print("Translation service configured:", service_id)

    languages = config.get("languages", {})

    if not languages:
        print(
            "RESULT: BLOCKED — "
            "No languages found in supported_languages.json"
        )
        return 1

    # ---------------------------------------------------------------
    # 3. Probe translation
    # ---------------------------------------------------------------

    print("\n[3] Translation service verification")
    print("-" * 70)

    failures = []

    for language_code, language_info in languages.items():

        if language_code == "en":
            continue

        translation_config = language_info.get("translation", {})

        capability = translation_config.get("status")

        if capability in {
            "not_configured",
            "disabled",
        }:
            print(
                f"{language_code:>4} : SKIP "
                f"(translation status: {capability})"
            )
            continue

        print(
            f"{language_code:>4} : testing English → {language_code} ...",
            end=" ",
            flush=True,
        )

        success, status = probe_translation(
            inference_key=inference_key,
            service_id=service_id,
            source_language="en",
            target_language=language_code,
        )

        if success:
            print("PASS")
        else:
            print(f"FAIL ({status})")
            failures.append((language_code, status))

    # ---------------------------------------------------------------
    # 4. Report ASR/TTS configuration
    # ---------------------------------------------------------------

    print("\n[4] Speech capability configuration")
    print("-" * 70)

    for language_code, language_info in languages.items():

        asr_status = language_info.get("asr", {}).get(
            "status",
            "unknown",
        )

        tts_status = language_info.get("tts", {}).get(
            "status",
            "unknown",
        )

        print(
            f"{language_code:>4} : "
            f"ASR={asr_status}, "
            f"TTS={tts_status}"
        )

    # ---------------------------------------------------------------
    # 5. Final result
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)

    if failures:
        print("RESULT: FAIL")
        print("\nFailed translation probes:")

        for language_code, status in failures:
            print(f"  - {language_code}: {status}")

        print(
            "\nCheck the Bhashini service ID, inference key, "
            "and configured language support."
        )

        return 1

    print("RESULT: PASS")
    print(
        "Configured translation probes completed successfully."
    )

    print(
        "\nNote: This verifies text translation only. "
        "It does not verify real microphone ASR or TTS audio."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())