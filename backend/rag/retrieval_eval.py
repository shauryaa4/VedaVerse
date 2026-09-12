"""
VEC-06 — Manual retrieval evaluation.

Not a pytest suite. This is a judgment-call script: it runs a fixed set of
realistic queries through the real chain (classify -> route ->
build_where_clause -> query) against the real Chroma collection, and prints
what comes back so a human can eyeball whether retrieval is actually pulling
the right law for the right product.

It DOES include mechanical assertions for the one thing that's NOT a judgment
call: every chunk returned for a query must have jurisdiction/legal_regime
metadata that matches what routing.py said the query should be filtered to.
If that fails, it's a real bug (a where-clause or ingestion bug), not a
"maybe the content's a bit off" situation, so it's flagged loudly.

Prerequisite: the corpus must already be ingested (run
scripts/ingest_corpus.py first). This script does NOT call the LLM and does
NOT need GEMINI_API_KEY — Chroma's bundled embedding model runs locally.

Run with:
    python -m backend.rag.retrieval_eval
or:
    python backend/rag/retrieval_eval.py
"""

from dataclasses import dataclass, field

from backend.logic.classification import apply_classification_to_pip
from backend.logic.routing import route
from backend.models.pip import ProductIntelligenceProfile
from backend.services.vector_store import (
    build_where_clause,
    get_client,
    get_or_create_collection,
    query as vector_query,
)

TOP_K = 5
PERSIST_DIR = "./chroma_data"


@dataclass
class EvalCase:
    name: str                      # human label, tied to the routing.py row it exercises
    pip_kwargs: dict                # kwargs to build ProductIntelligenceProfile
    question: str                   # the actual retrieval query text
    expected_regimes: list[str] = field(default_factory=list)  # for the mechanical check


# One case per row in routing.py's _INDIA_ROWS / _INTERNATIONAL_ROWS, so every
# regime mapping gets exercised at least once, plus one unresolved-fallback case.
CASES: list[EvalCase] = [
    EvalCase(
        name="india / classical_generic / patentability",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["patentability"],
            product=dict(
                classical_basis="yes",
                classical_reference="Charaka Samhita, Sutrasthana",
                novelty="existing",
                intended_use="therapeutic",
                composition=[{"ingredient": "Ashwagandha root powder", "is_active": True}],
            ),
        ),
        question="Can a classical Ayurvedic formulation with no modification be patented in India?",
        expected_regimes=["patent_law", "biodiversity_abs"],
    ),
    EvalCase(
        name="india / proprietary / patentability",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["patentability"],
            product=dict(
                classical_basis="partial",
                novelty="modified",
                intended_use="therapeutic",
                development_status="prototype",
                composition=[{"ingredient": "Curcumin", "is_active": True}],
            ),
        ),
        question="What novelty and inventive-step requirements apply to a modified herbal formulation seeking a patent?",
        expected_regimes=["patent_law", "biodiversity_abs"],
    ),
    EvalCase(
        name="india / new_drug / regulatory_category",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["regulatory_category"],
            product=dict(
                classical_basis="no",
                novelty="new_combination",
                intended_use="therapeutic",
                development_status="concept",
                composition=[{"ingredient": "Novel synthetic compound X", "is_active": True}],
            ),
        ),
        question="What regulatory pathway applies to a new therapeutic combination with no traditional-use precedent?",
        expected_regimes=["drug_regulation"],
    ),
    EvalCase(
        name="india / phytopharmaceutical / regulatory_category",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["regulatory_category"],
            product=dict(
                classical_basis="partial",
                novelty="unknown",
                intended_use="therapeutic",
                composition=[
                    {"ingredient": "Withaferin A extract", "quantity": "500", "unit": "mg", "is_active": True}
                ],
            ),
        ),
        question="What is the regulatory definition of a phytopharmaceutical drug in India?",
        expected_regimes=["drug_regulation"],
    ),
    EvalCase(
        name="india / nutraceutical_ayurveda_aahar / regulatory_category",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["regulatory_category"],
            product=dict(
                intended_use="food_supplement",
                composition=[{"ingredient": "Triphala extract", "is_active": True}],
            ),
        ),
        question="What FSSAI rules apply to an Ayurveda-based dietary supplement?",
        expected_regimes=["food_regulation"],
    ),
    EvalCase(
        name="india / cosmetic / regulatory_category",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["regulatory_category"],
            product=dict(
                intended_use="cosmetic",
                composition=[{"ingredient": "Neem oil", "is_active": True}],
            ),
        ),
        question="What regulatory category covers a herbal cosmetic product in India?",
        expected_regimes=["drug_regulation"],
    ),
    EvalCase(
        name="india / * / trademark",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["trademark"],
            product=dict(intended_use="therapeutic"),
        ),
        question="How do I register a brand name for an Ayurvedic product in India?",
        expected_regimes=["trademark_law"],
    ),
    EvalCase(
        name="india / * / abs_relevance",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["abs_relevance"],
            product=dict(
                biological_origin_known="yes",
                biological_origin_region="Western Ghats",
            ),
        ),
        question="Do I need Access and Benefit Sharing approval to commercialize a product using a native plant?",
        expected_regimes=["biodiversity_abs"],
    ),
    EvalCase(
        name="india / unresolved fallback / patentability",
        pip_kwargs=dict(
            jurisdiction="india",
            objective=["patentability"],
            product=dict(),  # deliberately empty -> classify() falls through to "unresolved"
        ),
        question="Can this product be patented?",
        expected_regimes=["patent_law"],
    ),
    EvalCase(
        name="international / * / patentability",
        pip_kwargs=dict(
            jurisdiction="international",
            objective=["patentability"],
            product=dict(intended_use="therapeutic"),
        ),
        question="What does TRIPS Article 27 say about patentable subject matter?",
        expected_regimes=["treaty_patent"],
    ),
    EvalCase(
        name="international / * / abs_relevance",
        pip_kwargs=dict(
            jurisdiction="international",
            objective=["abs_relevance"],
            product=dict(biological_origin_known="yes"),
        ),
        question="What does the Nagoya Protocol require for access to genetic resources?",
        expected_regimes=["treaty_abs", "wipo_gratk"],
    ),
    EvalCase(
        name="international / * / prior_art",
        pip_kwargs=dict(
            jurisdiction="international",
            objective=["prior_art"],
            product=dict(intended_use="therapeutic"),
        ),
        question="What disclosure obligations exist for traditional knowledge used as prior art?",
        expected_regimes=["wipo_gratk"],
    ),
]


def _build_pip(pip_kwargs: dict) -> ProductIntelligenceProfile:
    kwargs = dict(pip_kwargs)
    kwargs["product"] = kwargs.get("product", {})
    return ProductIntelligenceProfile(**kwargs)


def run() -> None:
    client = get_client(PERSIST_DIR)
    collection = get_or_create_collection(client)

    total = collection.count()
    print(f"Collection '{collection.name}' has {total} chunks.")
    if total == 0:
        print(
            "\n⚠️  Collection is empty. Run `python scripts/ingest_corpus.py` "
            "first, then re-run this script.\n"
        )
        return

    any_mismatch = False

    for case in CASES:
        print("\n" + "=" * 100)
        print(f"CASE: {case.name}")
        print(f"QUESTION: {case.question}")

        pip = _build_pip(case.pip_kwargs)
        apply_classification_to_pip(pip)
        routing = route(pip.jurisdiction, pip.classification.category, pip.objective)
        where = build_where_clause(routing)

        print(f"  category resolved: {pip.classification.category} "
              f"(confidence: {pip.classification.confidence})")
        print(f"  matched_rows: {routing.matched_rows or '(none — fell through)'}")
        if routing.status_notes:
            print(f"  status_notes: {routing.status_notes}")
        print(f"  where clause: {where}")

        results = vector_query(collection, case.question, where=where, top_k=TOP_K)
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not ids:
            print("  -> NO CHUNKS RETURNED (would abstain)")
            continue

        print(f"  -> {len(ids)} chunk(s) returned:")
        for chunk_id, text, meta in zip(ids, documents, metadatas):
            snippet = text[:140].replace("\n", " ")
            print(f"     [{chunk_id}] regime={meta.get('legal_regime')} "
                  f"jurisdiction={meta.get('jurisdiction')} doc={meta.get('doc_id')}")
            print(f"         \"{snippet}...\"")

            # Mechanical check — not a judgment call. A chunk from the wrong
            # jurisdiction or an unexpected regime means the where-clause or
            # ingestion tagging is broken, not that the content is "a bit off".
            if meta.get("jurisdiction") != routing.jurisdiction:
                any_mismatch = True
                print(f"     ❌ MISMATCH: chunk jurisdiction={meta.get('jurisdiction')!r} "
                      f"but routing expected {routing.jurisdiction!r}")
            if case.expected_regimes and meta.get("legal_regime") not in case.expected_regimes:
                any_mismatch = True
                print(f"     ❌ MISMATCH: chunk legal_regime={meta.get('legal_regime')!r} "
                      f"not in expected {case.expected_regimes}")

    print("\n" + "=" * 100)
    if any_mismatch:
        print("❌ One or more chunks had metadata that didn't match routing's expectations. "
              "Check the where-clause logic in vector_store.py or the corpus tagging.")
    else:
        print("✅ No jurisdiction/regime mismatches. Now read the actual chunk text above "
              "for each case and judge by eye whether it's the RIGHT law — that part "
              "this script can't do for you.")


if __name__ == "__main__":
    run()