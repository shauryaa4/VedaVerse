/**
 * Every value here is copy-pasted from the real backend model
 * (backend/models/pip.py) — not re-derived from the build spec doc, so it
 * can't silently drift from what the API actually accepts. If you add a
 * value on the backend, add it here too, in the same order.
 */

export const PROTECTION_TARGET_OPTIONS = [
  { value: 'formulation', label: 'A formulation / product' },
  { value: 'brand', label: 'A brand, name, or logo' },
  { value: 'process', label: 'A process or method' },
  { value: 'biological_resource', label: 'A biological resource' },
  { value: 'traditional_knowledge', label: 'Traditional knowledge' },
  { value: 'unsure', label: "I'm not sure yet" },
];

export const INTENDED_USE_OPTIONS = [
  { value: 'therapeutic', label: 'Therapeutic (internal medicinal use)' },
  { value: 'food_supplement', label: 'Food / dietary supplement' },
  { value: 'cosmetic', label: 'Cosmetic / personal care' },
  { value: 'agricultural', label: 'Agricultural' },
  { value: 'research', label: 'Research use only' },
  { value: 'other', label: 'Other' },
];

export const CLASSICAL_BASIS_OPTIONS = [
  { value: 'yes', label: 'Yes, based on a known classical formulation' },
  { value: 'no', label: 'No' },
  { value: 'partial', label: 'Partially — inspired by, but modified from, a classical formulation' },
  { value: 'unknown', label: "Don't know" },
];

export const NOVELTY_OPTIONS = [
  { value: 'existing', label: 'Existing — matches a known formulation exactly' },
  { value: 'modified', label: 'Modified — known ingredients, changed ratios or method' },
  { value: 'new_combination', label: 'New combination — new ingredients or new indication' },
  { value: 'unknown', label: "Don't know" },
];

export const INGREDIENT_SOURCE_OPTIONS = [
  { value: 'plant', label: 'Plant' },
  { value: 'animal', label: 'Animal' },
  { value: 'mineral', label: 'Mineral' },
  { value: 'microbial', label: 'Microbial' },
  { value: 'synthetic', label: 'Synthetic' },
];

export const DEVELOPMENT_STATUS_OPTIONS = [
  { value: 'concept', label: 'Concept only' },
  { value: 'prototype', label: 'Prototype' },
  { value: 'developed', label: 'Developed' },
  { value: 'marketed', label: 'Already marketed' },
  { value: 'filed_ip', label: 'IP already filed' },
];

export const OBJECTIVE_OPTIONS = [
  { value: 'patentability', label: 'Can I patent this?' },
  { value: 'regulatory_category', label: 'What regulatory category does this fall under?' },
  { value: 'trademark', label: 'Trademark / brand protection' },
  { value: 'prior_art', label: 'Prior art — has this been done before?' },
  { value: 'abs_relevance', label: 'Access & Benefit-Sharing (ABS) obligations' },
  { value: 'legal_pathway', label: 'What is the overall legal pathway?' },
  { value: 'general', label: 'General guidance' },
];

// Purely a UX nicety for the composition autocomplete (native <datalist>) —
// not sent to the backend, not a controlled vocabulary of any kind.
export const COMMON_INGREDIENTS = [
  'Ashwagandha', 'Shatavari', 'Turmeric (Haldi)', 'Neem', 'Tulsi (Holy Basil)',
  'Brahmi', 'Guduchi (Giloy)', 'Triphala', 'Amla', 'Ginger (Sunthi)',
  'Licorice (Yashtimadhu)', 'Guggul', 'Arjuna', 'Punarnava', 'Bhringraj',
  'Vidanga', 'Pippali', 'Haritaki', 'Bibhitaki', 'Manjistha',
];

export const CATEGORY_LABELS = {
  classical_generic: 'Classical / Generic',
  proprietary: 'Proprietary',
  new_drug: 'New Drug',
  phytopharmaceutical: 'Phytopharmaceutical',
  nutraceutical_ayurveda_aahar: 'Nutraceutical (Ayurveda-Aahar)',
  cosmetic: 'Cosmetic',
  unresolved: 'Unresolved',
};
