from backend.models.bhashini import TranslationResult

# lang_code -> { native_phrase: english_translation }
# Add ONE rehearsed entry per language you actually plan to demo.
TO_EN: dict[str, dict[str, str]] = {
    "hi": {
        "क्या हल्दी का पेटेंट कराया जा सकता है": "can turmeric be patented",
    },
    # "ta": { "...": "..." },
    # "bn": { "...": "..." },
}

# lang_code -> { english_phrase_fragment: native_translation }
# Use short fragments of your pipeline's actual answer text —
# translate_out does substring matching, not exact matching.
FROM_EN: dict[str, dict[str, str]] = {
    "hi": {
        "insufficient authoritative evidence": "पर्याप्त प्रामाणिक साक्ष्य नहीं है",
    },
    # "ta": { "...": "..." },
    # "bn": { "...": "..." },
}


def _normalize(text: str) -> str:
    return text.strip().lower()


def translate_in(text: str, source_lang: str) -> TranslationResult:
    """
    Mock native-language -> English translation.
    If source_lang is already 'en', pass through unchanged.
    """
    if source_lang == "en":
        return TranslationResult(
            original_text=text,
            translated_text=text,
            source_lang="en",
            target_lang="en",
            matched_known_phrase=True,
            mock=True,
        )

    lookup = TO_EN.get(source_lang, {})
    key = _normalize(text)
    for k, v in lookup.items():
        if _normalize(k) == key:
            return TranslationResult(
                original_text=text,
                translated_text=v,
                source_lang=source_lang,
                target_lang="en",
                matched_known_phrase=True,
                mock=True,
            )

    # Fallback: no rehearsed match. Never crash the demo.
    return TranslationResult(
        original_text=text,
        translated_text=f"[UNRECOGNIZED DEMO INPUT ({source_lang}) — mock translation unavailable] {text}",
        source_lang=source_lang,
        target_lang="en",
        matched_known_phrase=False,
        mock=True,
    )


def translate_out(text: str, target_lang: str) -> TranslationResult:
    """
    Mock English -> native-language translation of the final answer.
    """
    if target_lang == "en":
        return TranslationResult(
            original_text=text,
            translated_text=text,
            source_lang="en",
            target_lang="en",
            matched_known_phrase=True,
            mock=True,
        )

    lookup = FROM_EN.get(target_lang, {})
    key = _normalize(text)
    for k, v in lookup.items():
        if _normalize(k) in key:  # substring match — answers are longer than the key phrase
            return TranslationResult(
                original_text=text,
                translated_text=v,
                source_lang="en",
                target_lang=target_lang,
                matched_known_phrase=True,
                mock=True,
            )

    return TranslationResult(
        original_text=text,
        translated_text=f"[TRANSLATION UNAVAILABLE ({target_lang}) — DEMO MOCK] {text}",
        source_lang="en",
        target_lang=target_lang,
        matched_known_phrase=False,
        mock=True,
    )
