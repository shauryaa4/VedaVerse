# Presenter cheat sheet: how VedaVerse works today

## 30-second explanation

“VedaVerse collects product facts in a Product Intelligence Profile, applies deterministic classification and routing rules, and offers separate ABS and offline TKDL analyses. For legal questions, it retrieves passages from a curated corpus, drafts an explanation, checks citation overlap against the retrieved passages, and can abstain when evidence is missing or weak. Today these are connected tools, not one automated end-to-end legal decision.”

## 60-second explanation

“A user starts with a product intake: composition, intended use, development stage, objective, and any known biological source facts. The backend stores those in a PIP and classifies the product using deterministic code. The legal query route uses the classification and objective to select legal regimes, searches the shared Chroma collection built from the repository corpus, and asks the language model to explain the retrieved text. The API then checks whether citation markers point to retrieved chunks and applies confidence/abstention handling. ABS is a separate fact-driven engine that can optionally query the same Chroma collection for biodiversity-law passages; TKDL is a separate offline source-derived record search. The current frontend shows them in separate tabs, and it does not merge their results into one final report.”

## ABS (2–3 lines)

“ABS is a deterministic assessment driven by PIP plus structured ABS facts. It returns pathway, missing-information, authority, citations, evidence status, and escalation fields. Its full structured output is not currently displayed in the ABS screen, so I’ll describe only what the UI actually shows.”

## TKDL (2–3 lines)

“TKDL searches a local archive of source-derived records for ingredient overlap. It is explicitly not connected to the live TKDL service. A match is a research lead, not an ABS conclusion, medical assessment, or automatic patentability decision.”

## RAG (2–3 lines)

“The `/query` path routes the case, retrieves chunks from the shared Chroma legal corpus, and uses an LLM to draft an answer grounded in those chunks. The corpus is in Git; its generated Chroma index is not, so deployment/demo setup must ingest it.”

## Citation verification (2–3 lines)

“Citation markers are matched to the retrieved chunks, and a lexical overlap heuristic marks support and can remove weakly supported sentences. This helps trace an answer back to source text; it is not semantic verification or proof that a legal interpretation is correct.”

## Evidence flow (2–3 lines)

“The query response carries retrieved chunk references and citation status, then confidence logic may answer, hedge, or abstain. ABS has its own evidence status and optional source grounding. Those evidence paths are not yet unified across RAG, ABS, and TKDL.”

## Boundary phrases for the presenter

- Say “the current prototype classifies this input as…” rather than “the law classifies this product as…”.
- Say “the archive found an ingredient-overlap record” rather than “TKDL has ruled this patent invalid”.
- Say “the citation check found lexical overlap with this retrieved passage” rather than “the citation proves the conclusion”.
- When a fact is missing or conflicting, say so and request human review; do not fill it in from a product name.
