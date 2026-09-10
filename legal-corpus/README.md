# Legal Corpus

This directory contains structured legal documents and metadata for Indian and international legal frameworks, per the IP-SAKTI Sahayak demo build spec (§6).

## Structure

- `india/` — Indian laws, rules, and regulatory documents
- `international/` — International treaties, protocols, and agreements (not yet started -- see status below)
- `manifest.json` — Corpus-level manifest, auto-aggregated from each document directory's `meta.json`
- `corpus_validation.csv` — Validation and source-tracking, one row per required document (built or not-yet-built)
- `_template.meta.json` — Template for document-level metadata

Each legal instrument has its own directory. Every `.md` file inside a document directory carries a YAML frontmatter metadata block (doc_id, jurisdiction, legal_regime, document_name, document_type, section_or_article, product_class_tags, date_enacted, last_verified_date, source_url, status_note); each document directory also has a `meta.json` that mirrors those blocks for easy programmatic loading by the chunking/ingestion pipeline.

## Status (as of 2026-09-11, part 2 of ongoing corpus completion)

**India corpus: 7/7 P0+P1 documents complete.**

| Doc | Status |
|---|---|
| Patents Act 1970 | Done (§3(p), §3(d), §10, definitions) |
| Patents Rules 2003 (as amended) | Done (biological-material disclosure, priority declaration) |
| Biological Diversity Act 2002 (as amended 2023) | Done (definitions, §§3-7, §18) |
| Biological Diversity Rules 2024 | Done (Rules 13-20) |
| Drugs and Cosmetics Act & Rules | Done (§3(a), §3(h), Rule 158B summary, Rule 2(eb)/122E phytopharma) |
| FSSAI Ayurveda-Aahar Regulations | Done (scope/definition, labelling) |
| Trade Marks Act 1999 | **Done** (§2(1)(zb)/(m) definitions, §18(1) filing, §9 absolute grounds — full text, verbatim) |

**International corpus: 1/5 documents complete.**

| Doc | Status |
|---|---|
| TRIPS Agreement | **Done** (Art.1 general obligations, Art.27 patentable subject matter — both verbatim) |
| Convention on Biological Diversity | Not started — P0 |
| Nagoya Protocol | Not started — P0 |
| WIPO GRATK Treaty 2024 | Not started — P0, needs fresh ratification-count verification |
| PCT (basics) | Not started — P1 |

None of the above has had a legal-mentor sign-off yet — treat every file as "needs review" until someone does that pass, per the team's own risk log.

**Two things flagged during this pass, not silently fixed elsewhere:**
- `drugs-and-cosmetics-act/drug-category-definitions.md` includes Rule 158B as a **summary, not verbatim text** (exact Gazette wording not independently re-verified) — everything else in the India corpus is verbatim primary text.
- `corpus_validation.csv` previously used `INTL-1`…`INTL-5` for the international rows while `manifest.json`/the task brief use `INT-1`…`INT-5` — this is exactly the kind of doc_id drift SHAU-D3-05's acceptance criteria warns against. Corrected to `INT-1`…`INT-5` across the csv to match the canonical §0 table in `shau-corpus-tasks.md`.
- TRIPS Art.1/Art.27 text was verified against IP-PorTal's article-by-article TRIPS mirror (which itself states it's checked against WTO.org) rather than wto.org directly — wto.org wasn't fetchable in this session. Worth a direct WTO.org spot-check before the demo if anyone has the chance.
