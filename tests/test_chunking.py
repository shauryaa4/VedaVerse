"""
Tests for VEC-02. Run with: pytest -v tests/test_chunking.py

Fixtures under tests/fixtures/vec_test_corpus/ deliberately mirror the THREE
metadata patterns actually found in the real corpus as of this writing:
  - sample-act/       -> inline YAML frontmatter (Patents Act style)
  - sample-rules/      -> per-folder meta.json (Patents Rules style)
  - no-metadata-example/ -> neither (Biological Diversity Act style, 2 files)
"""

from pathlib import Path

from backend.rag.chunking import load_chunks_from_directory

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "vec_test_corpus"


def test_loads_all_real_content_files_not_scaffolding():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    # 2 from sample-act + 1 from sample-rules + 1 from no-metadata-example = 4
    assert len(chunks) == 4
    source_names = {Path(c.source_file).name for c in chunks}
    assert "meta.json" not in source_names  # scaffolding file must never become a chunk


def test_frontmatter_style_parsed_correctly():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    section_1 = next(c for c in chunks if c.section_or_article == "1")
    assert section_1.doc_id == "TEST-1"
    assert section_1.jurisdiction == "india"
    assert section_1.legal_regime == "test_law"
    assert section_1.document_type == "act"
    assert section_1.product_class_tags == ["classical_generic"]
    assert section_1.metadata_source == "frontmatter"
    assert "section 1 of the sample test act" in section_1.text
    assert "---" not in section_1.text  # frontmatter block must be stripped from body


def test_meta_json_style_parsed_correctly():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    rule = next(c for c in chunks if c.doc_id == "TEST-2")
    assert rule.legal_regime == "test_law"
    assert rule.document_type == "rule"
    assert rule.section_or_article == "Rule 5"
    assert rule.metadata_source == "meta_json"
    assert "Rule 5 of the sample test rules" in rule.text


def test_missing_metadata_degrades_gracefully_instead_of_crashing():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    orphan = next(c for c in chunks if c.metadata_source == "missing")
    assert orphan.doc_id is None
    assert orphan.legal_regime is None
    # jurisdiction still best-effort inferred from folder path so it's at
    # least findable by a jurisdiction-only fallback retrieval
    assert orphan.jurisdiction == "india"
    assert "deliberately has no frontmatter" in orphan.text
    assert orphan.chunk_id.startswith("missing:")


def test_chunk_id_format():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    section_2 = next(c for c in chunks if c.section_or_article == "2")
    assert section_2.chunk_id == "TEST-1:2"


def test_oversized_flag_does_not_trigger_on_normal_short_sections():
    chunks = load_chunks_from_directory(FIXTURE_ROOT)
    assert all(not c.oversized for c in chunks)  # all fixtures are short test snippets


def test_oversized_flag_does_trigger_on_long_text(tmp_path):
    long_folder = tmp_path / "india" / "long-doc"
    long_folder.mkdir(parents=True)
    long_file = long_folder / "big-section.md"
    long_text = " ".join(["word"] * 500)  # ~650 estimated tokens, over the 450 threshold
    long_file.write_text(
        f"---\ndoc_id: TEST-3\njurisdiction: india\nlegal_regime: test_law\n"
        f"document_type: act\nsection_or_article: \"1\"\nproduct_class_tags: []\n---\n\n{long_text}\n"
    )
    chunks = load_chunks_from_directory(tmp_path)
    assert len(chunks) == 1
    assert chunks[0].oversized is True
