from backend.logic.language import (
    _protect_citations,
    _restore_citations,
)


def test_english_input_is_unchanged():
    from backend.logic.language import translate_to_english

    question = "Can turmeric be patented?"

    assert translate_to_english(question, "en") == question


def test_citation_markers_are_protected():
    text = (
        "Turmeric cannot be patented as such. "
        "[IN-2:3(p)]"
    )

    protected, replacements = _protect_citations(text)

    assert "[IN-2:3(p)]" not in protected
    assert "__CITATION_0__" in protected
    assert replacements["__CITATION_0__"] == "[IN-2:3(p)]"


def test_citation_markers_are_restored():
    text = (
        "हल्दी को ऐसे पेटेंट नहीं कराया जा सकता। "
        "__CITATION_0__"
    )

    restored = _restore_citations(
        text,
        {
            "__CITATION_0__": "[IN-2:3(p)]"
        },
    )

    assert restored.endswith("[IN-2:3(p)]")


def test_multiple_citations_are_preserved():
    text = (
        "First claim. [IN-1:3(p)] "
        "Second claim. [IN-2:s12]"
    )

    protected, replacements = _protect_citations(text)

    assert "__CITATION_0__" in protected
    assert "__CITATION_1__" in protected

    restored = _restore_citations(
        protected,
        replacements,
    )

    assert restored == text