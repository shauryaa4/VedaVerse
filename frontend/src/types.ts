export type Jurisdiction = 'india' | 'international'

export type ProtectionTarget =
  | 'formulation'
  | 'brand'
  | 'process'
  | 'biological_resource'
  | 'traditional_knowledge'
  | 'unsure'

export type IntendedUse =
  | 'therapeutic'
  | 'food_supplement'
  | 'cosmetic'
  | 'agricultural'
  | 'research'
  | 'other'

export type ClassicalBasis = 'yes' | 'no' | 'partial' | 'unknown'

export type Novelty = 'existing' | 'modified' | 'new_combination' | 'unknown'

export type IngredientSource = 'plant' | 'animal' | 'mineral' | 'microbial' | 'synthetic'

export type DevelopmentStatus =
  | 'concept'
  | 'prototype'
  | 'developed'
  | 'marketed'
  | 'filed_ip'

export type Objective =
  | 'patentability'
  | 'regulatory_category'
  | 'trademark'
  | 'prior_art'
  | 'abs_relevance'
  | 'legal_pathway'
  | 'general'

export type Category =
  | 'classical_generic'
  | 'proprietary'
  | 'new_drug'
  | 'phytopharmaceutical'
  | 'nutraceutical_ayurveda_aahar'
  | 'cosmetic'
  | 'unresolved'

export type Confidence = 'high' | 'medium' | 'low'

export interface Composition {
  ingredient: string
  quantity: string
  unit: string
  is_active: boolean
}

export interface Classification {
  category: Category
  reasons: string[]
  confidence: Confidence
  unresolved_flags?: string[]
}

export interface Session {
  session_id: string
  jurisdiction: Jurisdiction | null
  product: {
    name: string
    composition: Composition[]
    intended_use: IntendedUse | null
    classical_basis: ClassicalBasis | null
    classical_reference: string
    novelty: Novelty | null
    ingredient_sources: IngredientSource[]
    geographic_origin: string
    biological_origin_known: boolean | null
    biological_origin_region: string
    development_status: DevelopmentStatus | null
  }
  protection_target: ProtectionTarget | null
  objective: Objective[]
  classification: Classification | null
}

export type AnswerConfidence = 'high' | 'medium' | 'low' | 'abstain'

export interface Citation {
  doc_id: string
  section: string
  excerpt: string
}

export interface AskResponse {
  answer: string
  citations: Citation[]
  confidence: AnswerConfidence
  abstained: boolean
}

// --- API response types (matching real backend contracts) ---

export interface TKDLIngredient {
  name: string
  scientific_name: string
  traditional_name: string
  source_category: string
  part_used: string
  processing: string
}

export interface TKDLClosestRecord {
  record_id: string
  formulation_name: string
  source_text: string
  formulation_type: string
  knowledge_known_since_years: number
  ingredients: TKDLIngredient[]
  therapeutic_use: string[]
}

export interface TKDLAssessment {
  risk_level: 'high' | 'medium' | 'low' | 'none'
  closest_record: TKDLClosestRecord | null
  what_was_already_known: string[]
  what_appears_different: string[]
  potential_novel_features: string[]
  reasoning: string[]
  mock: boolean
  disclaimer: string
}

export interface TKDLSearchResponse {
  assessment: TKDLAssessment
  matches: unknown[]
  mock: boolean
}

export type ABSRelevance = 'likely' | 'possible' | 'unlikely' | 'not_applicable'

export interface ABSAssessResponse {
  relevance: ABSRelevance
  reasoning: string[]
  applicable_authority_guidance: string[]
  ip_filing_flag: boolean
  ip_filing_note: string | null
  disclaimer: string
}

export interface ClassifyResponse {
  category: Category
  reasons: string[]
  confidence: Confidence
  unresolved_flags: string[]
}

export interface QueryResponse {
  answer_text: string
  used_chunks: Citation[]
  abstained: boolean
  abstain_reason: string | null
  status_notes: string[]
}

export type Screen =
  | 'landing'
  | 'jurisdiction'
  | 'questionnaire'
  | 'classification'
  | 'query'
  | 'answer'
  | 'tkdl'
  | 'abs'
