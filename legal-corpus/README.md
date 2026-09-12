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

## Status (as of 2026-09-12) — spec §6 minimum viable set complete, one content gap fixed

| Doc | doc_id | Sections | Status |
|---|---|---|---|
| Patents Act 1970 | IN-1 | 4 | Done |
| Patents Rules 2003 (as amended) | IN-2 | 2 | Done |
| Biological Diversity Act 2002 (as amended 2023) | IN-3 | 3 | Done |
| Biological Diversity Rules 2024 | IN-4 | 1 | Done |
| Drugs and Cosmetics Act & Rules | IN-5 | 3 | **Fixed — see gap below** |
| FSSAI Ayurveda-Aahar Regulations | IN-6 | 2 | Done |
| Trade Marks Act 1999 | IN-7 | 2 | Done |
| TRIPS (Art 1, 27) | INTL-1 | 2 | Done |
| CBD (Art 15) | INTL-2 | 1 | Done |
| Nagoya Protocol (Art 5, 6) | INTL-3 | 1 | Done |
| WIPO GRATK Treaty (Art 3) | INTL-4 | 1 | Done — carries mandatory not-yet-in-force status note |
| PCT basics | INTL-5 | 1 | Done |

**12 documents, 23 sections total** (was 22). Every routing rule in the demo spec's §5 (Routing
Engine) table has a corpus doc behind it.

## Gap fixed 2026-09-12

`india/cosmetic/regulatory_category` retrieval was returning only the Section 3(a) "Ayurvedic,
Siddha or Unani drug" definition — because no file in `india/drugs-and-cosmetics-act/` actually
defined **"cosmetic."** Routing was working correctly (right document set, right jurisdiction); the
document set itself was just missing the clause. Added
`india/drugs-and-cosmetics-act/section-3aaa-cosmetic-definition.md` (Section 3(aaa), tagged
`product_class_tags: ["cosmetic"]`), sourced from the bare-act text and cleaned of amendment-bracket
artifacts. Wired into that directory's `meta.json` and the aggregated `manifest.json`/
`corpus_validation.csv`. No other content gaps were found against spec §6's minimum-viable-set
table — everything else is unchanged.

## 2026-09-11 dedup pass

Two docs briefly existed twice because two people built the same brief in parallel with different
folder names:

- **Drugs & Cosmetics Act** — `india/drugs-cosmetics-act/` and `india/drugs-and-cosmetics-act/` both
  existed with `doc_id: IN-5`. Kept `drugs-and-cosmetics-act/` (more thorough — also correctly flags
  that the spec's "2016 Rule amendment" is actually the 2015 Eighth Amendment Rules, G.S.R. 918(E)).
  Removed `drugs-cosmetics-act/`.
- **TRIPS** — `international/trips/` and `international/trips-agreement/` both existed, with
  *inconsistent doc_ids* (`INTL-1` vs `INT-1`). Kept `trips-agreement/` (more complete Article 1) and
  corrected its doc_id to the corpus-standard `INTL-1`. Removed `trips/`.
- Also removed two empty, never-populated placeholder folders left over from a failed scaffold: a
  literal directory named `{trips,cbd,nagoya-protocol,wipo-gratk,pct}` (brace expansion didn't run in
  whatever shell created it) and an empty `international/wipo-gratk-treaty/`.
- Added the missing `meta.json` entry for `india/trade-marks-act-1999/registrability-basics.md` (a
  genuinely new, non-duplicate file that existed but wasn't wired into the manifest).
- Added `status_note` to the two FSSAI files, which were the only pair still `null`, for consistency.

**If you're adding a new doc to this corpus, check `manifest.json` for the doc_id and folder name
first** — this dedup only happened because two people didn't know the other had started.

## Still open before the demo

1. **Nobody with legal training has reviewed any of this yet** — including the new cosmetic
   definition. Every file's `status_note` and the `reviewed_by` column in `corpus_validation.csv`
   flag this.
2. **Re-verify the WIPO GRATK ratification count** in `international/wipo-gratk/article-3-disclosure.md`
   close to the demo date — it was 4 of the required 15 at last check and moves as more States ratify.
3. Deliberately **cut per spec §6**: GI Act, Designs Act, Copyright Act, Drugs and Magic Remedies Act.
4. Gold test set (§17) and citation-verification wiring are downstream RAG-owner work, not corpus work.

## Note on structure

This corpus stays in the **one-subfolder-per-document, one-file-per-section** layout
(`india/<doc-slug>/<section-slug>.md` + a per-directory `meta.json`), aggregated into the top-level
`manifest.json`. If anyone proposes flattening this into one file per document, don't — the
ingestion/chunking pipeline is built against this layout.
