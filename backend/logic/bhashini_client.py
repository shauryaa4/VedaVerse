"""Authenticated Bhashini pipeline configuration and compute helpers."""

from __future__ import annotations

import os
from functools import lru_cache

import requests
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
DEFAULT_PIPELINE_ID = "64392f96daac500b55c543cd"
COMPUTE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
from backend.logic.languages import TRANSLATION_SERVICE_ID


class BhashiniError(RuntimeError):
    """Sanitized Bhashini configuration or inference failure."""


def _required_config_credentials() -> tuple[str, str]:
    user_id = (os.getenv("BHASHINI_USER_ID") or "").strip()
    api_key = (
        os.getenv("BHASHINI_ULCA_API_KEY")
        or os.getenv("BHASHINI_UDYAT_KEY")
        or ""
    ).strip()
    if not user_id or not api_key:
        raise BhashiniError(
            "Set BHASHINI_USER_ID and BHASHINI_ULCA_API_KEY from the Bhashini "
            "Udyat/ULCA My Profile page. These are separate from email and from "
            "the inference key."
        )
    return user_id, api_key


def _static_service_id(task_type: str, source_language: str, target_language: str) -> str:
    if task_type == "translation":
        return TRANSLATION_SERVICE_ID
    if task_type == "audio-lang-detection":
        return "bhashini/iitmandi/audio-lang-detection/gpu"
    if task_type == "asr":
        if source_language == "en":
            return "ai4bharat/whisper-medium-en--gpu--t4"
        if source_language in {"ta", "te", "kn", "ml"}:
            return "ai4bharat/conformer-multilingual-dravidian-gpu--t4"
        return "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
    if task_type == "tts":
        if source_language == "hi":
            return "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"
        return "Bhashini/IITM/TTS"
    raise BhashiniError(f"Unsupported Bhashini task: {task_type}.")


@lru_cache(maxsize=128)
def _resolve_cached(task_type: str, source_language: str, target_language: str) -> tuple[str, str, str, str]:
    user_id = (os.getenv("BHASHINI_USER_ID") or "").strip()
    ulca_key = (
        os.getenv("BHASHINI_ULCA_API_KEY")
        or os.getenv("BHASHINI_UDYAT_KEY")
        or ""
    ).strip()
    inference_key = (os.getenv("BHASHINI_INFERENCE_KEY") or "").strip()
    # A complete Udyat pair requests a per-task pipeline configuration. An
    # already-issued inference key can be used directly when no pair exists.
    if not (user_id and ulca_key):
        if inference_key:
            header_name = (os.getenv("BHASHINI_INFERENCE_HEADER") or "Authorization").strip()
            return (
                _static_service_id(task_type, source_language, target_language),
                COMPUTE_URL,
                header_name or "Authorization",
                inference_key,
            )
        _required_config_credentials()
    pipeline_id = (os.getenv("BHASHINI_PIPELINE_ID") or DEFAULT_PIPELINE_ID).strip()
    task_config: dict = {}
    language = {}
    if source_language:
        language["sourceLanguage"] = source_language
    if target_language:
        language["targetLanguage"] = target_language
    if language:
        task_config["language"] = language
    payload = {
        "pipelineTasks": [{"taskType": task_type, "config": task_config}],
        "pipelineRequestConfig": {"pipelineId": pipeline_id},
    }
    try:
        response = requests.post(
            CONFIG_URL,
            headers={
                "userID": user_id,
                "ulcaApiKey": ulca_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status in (400, 401, 403):
            message = (
                "Bhashini pipeline configuration rejected the ULCA credentials. "
                "Check that BHASHINI_USER_ID and BHASHINI_ULCA_API_KEY are the "
                "matching pair from the same Udyat profile."
            )
        else:
            message = f"Bhashini pipeline configuration failed (HTTP {status})."
        raise BhashiniError(message) from exc
    except requests.RequestException as exc:
        raise BhashiniError(
            f"Bhashini pipeline configuration request failed ({type(exc).__name__})."
        ) from exc
    except ValueError as exc:
        raise BhashiniError("Bhashini returned invalid pipeline configuration JSON.") from exc

    configs = data.get("pipelineResponseConfig") or []
    if not configs:
        raise BhashiniError("Bhashini has no configured model for this task/language pair.")

    config_entry = next(
        (entry for entry in configs if entry.get("taskType") == task_type),
        configs[0],
    )
    variants = config_entry.get("config") or []
    selected = next(
        (
            item for item in variants
            if item.get("language", {}).get("sourceLanguage", source_language) == source_language
            and item.get("language", {}).get("targetLanguage", target_language) == target_language
        ),
        variants[0] if variants else {},
    )
    endpoint = data.get("pipelineInferenceAPIEndPoint") or {}
    inference_key = endpoint.get("inferenceApiKey") or {}
    service_id = selected.get("serviceId")
    callback_url = endpoint.get("callbackUrl")
    header_name = inference_key.get("name")
    header_value = inference_key.get("value")
    if not all((service_id, callback_url, header_name, header_value)):
        raise BhashiniError("Bhashini config response is missing model or inference credentials.")
    return service_id, callback_url, header_name, header_value


def resolve_pipeline(task_type: str, source_language: str = "", target_language: str = "") -> dict:
    service_id, callback_url, header_name, header_value = _resolve_cached(
        task_type, source_language, target_language
    )
    return {
        "service_id": service_id,
        "callback_url": callback_url,
        "headers": {
            header_name: header_value,
            "Content-Type": "application/json",
            "Accept": "*/*",
        },
    }


def compute(payload: dict, task_type: str, source_language: str = "", target_language: str = "") -> dict:
    pipeline = resolve_pipeline(task_type, source_language, target_language)
    tasks = payload.get("pipelineTasks") or []
    if not tasks:
        raise BhashiniError("Bhashini compute request has no task.")
    tasks[0].setdefault("config", {})["serviceId"] = pipeline["service_id"]
    try:
        response = requests.post(
            pipeline["callback_url"],
            headers=pipeline["headers"],
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise BhashiniError(f"Bhashini inference request failed (HTTP {status}).") from exc
    except requests.RequestException as exc:
        raise BhashiniError(
            f"Bhashini inference request failed ({type(exc).__name__})."
        ) from exc
    except ValueError as exc:
        raise BhashiniError("Bhashini returned invalid inference JSON.") from exc
