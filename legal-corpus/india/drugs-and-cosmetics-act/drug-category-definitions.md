---
doc_id: IN-5
jurisdiction: india
legal_regime: drug_regulation
document_name: "Drugs and Cosmetics Act 1940 & Drugs and Cosmetics Rules 1945 (as amended)"
document_type: act
section_or_article: "Section 3(a), Section 3(h); Rule 158B (summarized)"
product_class_tags: ["classical_generic", "proprietary", "new_drug"]
date_enacted: "1940 (Act); 1945 (Rules); Rule 158B inserted 2010"
last_verified_date: "2026-09-11"
source_url: "https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/acts_rules/2016DrugsandCosmeticsAct1940Rules1945.pdf"
status_note: null
---

## Section 3(a) — "Ayurvedic, Siddha or Unani drug"

"Ayurvedic, Siddha or Unani drug" includes all medicines intended for internal or external use for or in the diagnosis, treatment, mitigation or prevention of disease or disorder in human beings or animals, and manufactured exclusively in accordance with the formulae described in the authoritative books of the Ayurvedic, Siddha and Unani Tibb systems of medicine specified in the First Schedule.

*(This is the "classical" branch — a formulation manufactured strictly per an authoritative-text formula falls here, not under clause (h) below.)*

## Section 3(h) — "patent or proprietary medicine"

"patent or proprietary medicine" means —

(i) in relation to Ayurvedic, Siddha or Unani Tibb systems of medicine, all formulations containing only such ingredients mentioned in the formulae described in the authoritative books of the Ayurvedic, Siddha or Unani Tibb systems of medicine specified in the First Schedule, but does not include a medicine which is administered by parenteral route and also a formulation included in the authoritative books as specified in clause (a);

(ii) in relation to any other systems of medicine, a drug which is a remedy or prescription presented in a form ready for internal or external administration of human beings or animals and which is not included in the edition of the Indian Pharmacopoeia for the time being or any other Pharmacopoeia authorised in this behalf by the Central Government after consultation with the Drugs Technical Advisory Board constituted under section 5.

*(This is the "proprietary" branch under clause (h)(i) — same authoritative-text ingredients as clause (a), but the formulation itself (ratio, combination, or presentation) is not itself one of the authoritative-book formulae. Clause (h)(ii) is the general/allopathic patent-or-proprietary-medicine definition and is included here only for contrast; it is not the ASU pathway.)*

## Rule 158B — classical vs. patent-or-proprietary licensing distinction (summarized, not verbatim)

Rule 158B of the Drugs and Cosmetics Rules 1945 (inserted 2010) is the licensing-stage provision that operationalizes the 3(a)/3(h) split: classical ASU drugs manufactured strictly per an authoritative-text formula are, in general licensing practice, treated as exempt from pre-market clinical safety-and-efficacy study requirements. For patent-or-proprietary ASU medicines under 3(h)(i) — and for any new ASU formulation, new combination, new indication, or one raising a safety issue — the licensing authority is empowered under Rule 158B to call for evidence of safety and efficacy (textual rationale from authoritative literature, published literature, and/or pilot study data; a full pilot study is required specifically where textual/literature support for the indication is not available).

**This paragraph is a summary of Rule 158B's effect, not a verbatim reproduction of the rule text** — secondary regulatory-affairs sources describe its practical operation consistently, but the exact operative clause wording was not independently re-verified against the Gazette-notified rule text at time of writing. Flag for legal-mentor sign-off before treating this specific paragraph as citable primary text; §3(a) and §3(h) above ARE verbatim statutory text and do not carry this caveat.

## Why this matters for classification (per build spec §4)

This is the statutory basis for the CLASSICAL_GENERIC vs. PROPRIETARY split used by the rule engine:
- `classical_basis = yes` AND unmodified formula/proportions → maps to Section 3(a) ("Ayurvedic, Siddha or Unani drug").
- `classical_basis = no/partial` AND `novelty = modified/new_combination` AND ASU ingredients only, non-parenteral → maps to Section 3(h)(i) ("patent or proprietary medicine").
- Anything introducing ingredients/indications with no authoritative-text precedent, or requiring new safety-efficacy proof, escalates toward NEW_DRUG (see Rule 122E, referenced in `phytopharmaceutical-definition.md` for the phytopharmaceutical-specific case).
