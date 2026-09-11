---
doc_id: IN-5
jurisdiction: india
legal_regime: drug_regulation
document_name: "Drugs and Cosmetics Rules 1945 (Eighth Amendment Rules 2015 / Rule 122E)"
document_type: rule
section_or_article: "Rule 2(eb) - phytopharmaceutical drug; Rule 122E - new drug"
product_class_tags: ["phytopharmaceutical", "new_drug"]
date_enacted: "1945"
last_verified_date: "2026-09-11"
source_url: "https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/New-Drugs/FAQs/New_Drugs_FAQs.doc"
status_note: "Built to close a gap flagged as P0 and 'not started' in a prior review. Compiled from CDSCO guidance documents; not yet legal-mentor reviewed -- see corpus_validation.csv."
---

Rule 2(eb). "Phytopharmaceutical drug" includes purified and standardised fraction with defined minimum four bio-active or phyto-chemical compounds (qualitatively and quantitatively assessed) of an extract of a medicinal plant or its part, for internal or external use of human beings or animals for diagnosis, treatment, mitigation or prevention of any disease or disorder, but does not include administration by the parenteral route.

Rule 122E. A phytopharmaceutical drug which has not been used in the country to any significant extent under the conditions prescribed, recommended or suggested in its labelling, and has not been recognised as effective and safe by the licensing authority for the proposed claims, is considered a "new drug" and must be approved by the Central Drugs Standard Control Organisation (CDSCO) before marketing.

How this differs from an Ayurvedic/Siddha/Unani (ASU) drug under Section 3(a)/3(h) of the Act: ASU drugs are whole/crude preparations manufactured exclusively per an authoritative-book formula. A phytopharmaceutical drug is instead a purified, standardised fraction of a plant extract with at least four identified and quantified phyto-chemical/bio-active compounds -- it is treated as a modern new drug requiring CDSCO approval, not as a classical Ayurvedic medicine, even though it is plant-derived. A phytopharmaceutical drug also cannot be combined with a synthetic drug, mineral, metal, or animal part, and lichens/fungal/algal/endophyte extracts are not eligible for this category.

Practical read for the classification engine: this is the operative test for the "Phytopharmaceutical" category in the rule engine (§4 of the demo spec) -- a formulation that is a standardised, multi-compound-quantified plant extract with a defined therapeutic claim (not a whole-herb classical preparation) routes here, and is treated as a New Drug requiring safety/efficacy evidence, distinct from both the classical-generic and the general new-drug branches.
