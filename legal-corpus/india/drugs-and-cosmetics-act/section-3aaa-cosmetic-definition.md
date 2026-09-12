---
doc_id: IN-5
jurisdiction: india
legal_regime: drug_regulation
document_name: "Drugs and Cosmetics Act 1940 (as amended)"
document_type: act
section_or_article: "Section 3(aaa) (definition of \"cosmetic\")"
product_class_tags: ["cosmetic"]
date_enacted: "1940 (Act); clause (aaa) inserted by later amendment"
last_verified_date: "2026-09-12"
source_url: "https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/acts_rules/2016DrugsandCosmeticsAct1940Rules1945.pdf"
status_note: "GAP FIX (2026-09-12): this section did not exist anywhere in the corpus. Flagged during the human-judgment review pass over routing/retrieval output -- india/cosmetic/regulatory_category queries were returning only Section 3(a) (the 'Ayurvedic, Siddha or Unani drug' definition, in drug-category-definitions.md) because no chunk in the corpus actually defined 'cosmetic.' Routing was working correctly; the underlying document set was simply missing this clause. Added from the bare-act text (cleaned of amendment-bracket artifacts, e.g. '5[7[(aaa)]' and trailing '10[*]'). Not yet legal-mentor reviewed, consistent with the rest of the corpus."
---

## Section 3(aaa) — "cosmetic"

"cosmetic" means any article intended to be rubbed, poured, sprinkled or sprayed on, or introduced into, or otherwise applied to, the human body or any part thereof for cleansing, beautifying, promoting attractiveness, or altering the appearance, and includes any article intended for use as a component of cosmetic.

*(For context, the immediately preceding clause, Section 3(aa), defines "the Board" -- the Ayurvedic, Siddha and Unani Drugs Technical Advisory Board for ASU drugs, or the Drugs Technical Advisory Board under section 5 for any other drug or cosmetic. Noted here only because both clauses appear together in the bare act; it is not itself decision-relevant to product classification and is not treated as its own chunk.)*

## Why this matters for classification and routing (per build spec §4-§5)

This is the statutory basis for the COSMETIC branch of the classification rule engine (`intended_use == "cosmetic"` → COSMETIC) and the corresponding routing row (`India + Cosmetic + regulatory_category → Drugs and Cosmetics Act (cosmetic provisions)`). Before this fix, a query routed to that row would retrieve only the Section 3(a) ASU-drug definition (see `drug-category-definitions.md`) with no chunk actually defining "cosmetic" itself -- an answer built from that alone could look like it was describing a drug-labelled cosmetic rather than answering what a cosmetic actually is under the Act.
