---
doc_id: IN-5
jurisdiction: india
legal_regime: drug_regulation
document_name: "Drugs and Cosmetics Rules 1945 (Eighth Amendment Rules, 2015 — Rule 2(eb)) and Rule 122E"
document_type: rule
section_or_article: "Rule 2(eb) (definition); Rule 122E (new-drug application)"
product_class_tags: ["phytopharmaceutical", "new_drug"]
date_enacted: "2015 (Rule 2(eb) inserted by G.S.R. 918(E), the Eighth Amendment Rules, 2015)"
last_verified_date: "2026-09-11"
source_url: "https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/acts_rules/2016DrugsandCosmeticsAct1940Rules1945.pdf"
status_note: "Shau's task brief (and the build spec) refers to this as the '2016 Rule amendment.' On verification, the operative insertion is the Drugs and Cosmetics Rules (Eighth Amendment), 2015 (G.S.R. 918(E)), not 2016. Flagging the discrepancy here rather than silently correcting the team's other documents -- routing/classification logic referencing 'the 2016 phytopharmaceutical amendment' should be understood as this same 2015 rule."
---

## Rule 2(eb) — "Phytopharmaceutical drug"

"Phytopharmaceutical drug" includes purified and standardised fraction with defined minimum four bio-active or phyto-chemical compounds (qualitatively and quantitatively assessed) of an extract of a medicinal plant or its part, for internal or external use of human beings or animals for diagnosis, treatment, mitigation or prevention of any disease or disorder, but does not include administration by parenteral route.

## Rule 122E — "new drug" (as applied to phytopharmaceuticals)

Rule 122E defines "new drug" to include, among other categories, a drug substance not previously used in the country to a significant extent under the conditions prescribed, recommended, or suggested in its labelling, and not recognised as effective and safe by the licensing authority under Rule 21 for the proposed claims. A phytopharmaceutical drug meeting the Rule 2(eb) definition is, by default, treated as a "new drug" under Rule 122E for regulatory-submission purposes — it is not automatically grandfathered in the way a strictly classical Section 3(a) formulation is.

## What distinguishes a phytopharmaceutical from a classical or proprietary ASU formulation

A phytopharmaceutical is a **purified, standardized fraction** (not a whole-herb or whole-extract preparation) with a **defined minimum of four qualitatively-and-quantitatively-assessed bio-active/phyto-chemical compounds**, carrying a defined therapeutic claim on that standardized basis. This is a materially different regulatory object from:
- a classical Section 3(a) formulation (whole preparation per an authoritative-text formula), or
- a Section 3(h)(i) patent-or-proprietary ASU medicine (still authoritative-text ingredients, just a non-classical combination/ratio).

Phytopharmaceutical drug approvals sit with the Central Drugs Standard Control Organization (CDSCO) under the Drugs and Cosmetics Rules generally (Schedule Y, Appendix I-B data requirements), rather than under the State-level ASU drug-licensing route that governs classical/proprietary Ayurvedic medicines.

## Why this matters for classification (per build spec §4)

Maps directly to the PHYTOPHARMACEUTICAL branch of the rule engine: `composition includes standardized/isolated phytoconstituents with defined therapeutic claims (not whole-herb classical prep)` → PHYTOPHARMACEUTICAL, with the Rule 2(eb)/Rule 122E pairing above as the statutory basis for why this is treated as its own regulatory category rather than folded into NEW_DRUG or PROPRIETARY.
