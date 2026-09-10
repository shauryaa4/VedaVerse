# Legal Corpus

This directory contains structured legal documents and metadata for Indian and international legal frameworks, per the IP-SAKTI Sahayak demo build spec (§6).

## Structure

- `india/` — Indian laws, rules, and regulatory documents
- `international/` — International treaties, protocols, and agreements (not yet started -- see status below)
- `manifest.json` — Corpus-level manifest, auto-aggregated from each document directory's `meta.json`
- `corpus_validation.csv` — Validation and source-tracking, one row per required document (built or not-yet-built)
- `_template.meta.json` — Template for document-level metadata

Each legal instrument has its own directory. Every `.md` file inside a document directory carries a YAML frontmatter metadata block (doc_id, jurisdiction, legal_regime, document_name, document_type, section_or_article, product_class_tags, date_enacted, last_verified_date, source_url, status_note); each document directory also has a `meta.json` that mirrors those blocks for easy programmatic loading by the chunking/ingestion pipeline.

## Status (as of 2026-09-11, part 1 of ongoing corpus completion)

| Doc | Status |
|---|---|
| Patents Act 1970 | Done (§3(p), §3(d), §10, definitions) |
| Patents Rules 2003 (as amended) | Done (biological-material disclosure, priority declaration) |
| Biological Diversity Act 2002 (as amended 2023) | Done (definitions, §§3-7, §18) |
| Biological Diversity Rules 2024 | Done (Rules 13-20) |
| Drugs and Cosmetics Act & Rules | **Done** (§3(a), §3(h), Rule 158B summary, Rule 2(eb)/122E phytopharma) |
| FSSAI Ayurveda-Aahar Regulations | Done (scope/definition, labelling) — *was already complete on disk, `corpus_validation.csv` had just gone stale; reconciled 2026-09-11* |
| Trade Marks Act 1999 | **Not started** — P1 |
| International corpus (TRIPS, CBD, Nagoya, WIPO GRATK, PCT) | **Not started** — P0/P1, see `corpus_validation.csv` |

None of the above has had a legal-mentor sign-off yet — treat every file as "needs review" until someone does that pass, per the team's own risk log. One item to flag explicitly: `drugs-and-cosmetics-act/drug-category-definitions.md` includes Rule 158B as a **summary, not verbatim text** (its exact Gazette wording wasn't independently re-verified) — everything else in that document and elsewhere in the India corpus so far is verbatim primary text.
