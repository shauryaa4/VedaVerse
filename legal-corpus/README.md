# Legal Corpus

Structured legal documents and metadata for Indian and international legal frameworks, per the
IP-SAKTI Sahayak demo build spec (§6).

## Structure

- `india/` — Indian laws, rules, and regulatory documents
- `international/` — International treaties and protocols
- `manifest.json` — Corpus-level manifest, auto-aggregated from each document directory's `meta.json`
- `corpus_validation.csv` — Validation and source-tracking, one row per required document
- `_template.meta.json` — Template for document-level metadata

Every `.md` file carries a YAML frontmatter metadata block (doc_id, jurisdiction, legal_regime,
document_name, document_type, section_or_article, product_class_tags, date_enacted,
last_verified_date, source_url, status_note). Each document directory also has a `meta.json`
mirroring those blocks for the ingestion/chunking pipeline to load directly.

## Status (as of 2026-09-11) — spec §6 minimum viable set is complete

| Doc | Status |
|---|---|
| Patents Act 1970 | Done |
| Patents Rules 2003 (as amended) | Done |
| Biological Diversity Act 2002 (as amended 2023) | Done |
| Biological Diversity Rules 2024 | Done |
| Drugs and Cosmetics Act & Rules | Done |
| FSSAI Ayurveda-Aahar Regulations | Done |
| Trade Marks Act 1999 | Done (§9 absolute grounds — the P1 minimum) |
| TRIPS (Art 1, 27) | Done |
| CBD (Art 15) | Done |
| Nagoya Protocol (Art 5, 6) | Done |
| WIPO GRATK Treaty (Art 3) | Done — carries mandatory not-yet-in-force status note |
| PCT basics | Done |

**Every routing rule in the demo spec's §5 (Routing Engine) table now has a corpus doc behind it**,
including both India-vs-International tracks for patentability and ABS.

## Still open before the demo

1. **Nobody with legal training has reviewed any of this yet.** Every file's `status_note` and the
   `reviewed_by` column in `corpus_validation.csv` flag this. Get a mentor to skim it, especially the
   Biological Diversity Act and GRATK files.
2. **Re-verify the WIPO GRATK ratification count** in `international/wipo-gratk/article-3-disclosure.md`
   close to the demo date — it was 4 of the required 15 at last check and moves as more States ratify.
3. Deliberately **cut per spec §6**: GI Act, Designs Act, Copyright Act, Drugs and Magic Remedies Act —
   these are explicitly out of scope for the demo, listed here so nobody re-adds them by accident.
4. Gold test set (§17 of the spec) and citation-verification wiring against this corpus are downstream
   work for whoever owns RAG/retrieval, not part of this corpus deliverable.
