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

export interface ABSFactProfileInput {
  applicant?: {
    entity_category?: string
    applicant_type?: string
    nationality?: string
    incorporation_country?: string
    foreign_participation_or_control?: boolean
  }
  resource?: {
    biological_resource_involved?: boolean
    resource_name?: string
    scientific_name?: string
    resource_type?: string
    resource_part?: string
    quantity?: number
    unit?: string
    country_of_origin?: string
    origin_status?: string
    geographical_location?: string
  }
  access?: {
    access_method?: string
    source_type?: string
    cultivated?: boolean
    wild_collected?: boolean
    artificially_propagated?: boolean
    market_or_trader?: boolean
    supplier?: string
    community?: string
    institution?: string
  }
  tk?: {
    associated_traditional_knowledge?: boolean
    tk_type?: string
    tk_source?: string
    tk_codified?: boolean
    tk_community_based?: boolean
  }
  activity?: {
    activities?: string[]
  }
  ipr?: {
    ipr_stage?: string
    ipr_type?: string
    jurisdiction_filed?: string
  }
  certificate_of_origin?: {
    certificate_required?: boolean
    certificate_available?: boolean
    certificate_status?: string
    issuing_authority?: string
    note?: string
  }
  transfer?: {
    transfer_involved?: boolean
    transfer_type?: string
    transferee_type?: string
    transferee_country?: string
  }
  annual_turnover_inr?: number
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
  abs_facts?: ABSFactProfileInput | null
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

// --- API response types ---

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
export type ABSStatus = 'STRONG' | 'CONDITIONAL' | 'INSUFFICIENT_INFORMATION' | 'CONFLICTING' | 'ESCALATION_RECOMMENDED'

export interface ABSTriggeredRule {
  rule_id: string
  rule_name: string
  section_or_rule: string
  description: string
  authority: string
  required_form?: string | null
  source_doc_id: string
  source_provision: string
}

export interface ABSExemptionCheck {
  exemption_id: string
  name: string
  source_provision: string
  conditions_checked?: Record<string, any>
  is_triggered: boolean
  reason: string
  source_doc_id: string
}

export interface ABSFormRequirement {
  form_id: string
  form_name: string
  purpose: string
  authority: string
  fee: string
  required_documents: string[]
  source_doc_id: string
}

export interface ABSAuthorityRouting {
  authority_name: string
  authority_level: string
  jurisdiction_scope: string
  reasons: string[]
  status: string
}

export interface BenefitSharingProfile {
  applicable: boolean
  basis?: string | null
  benefit_type?: string | null
  turnover_inr?: number | null
  turnover_band?: string | null
  rate_or_slab?: string | null
  indicative_amount_inr?: number | null
  special_condition?: string | null
  calculation_status: string
  disclaimer: string
  source?: string | null
}

export interface CertificateOfOriginProfile {
  certificate_required: boolean
  certificate_available: boolean
  certificate_status: 'REQUIRED' | 'PROVIDED' | 'MISSING' | 'NOT_APPLICABLE'
  issuing_authority?: string | null
  note?: string | null
}

export interface ABSCitation {
  doc_id: string
  document_name: string
  document_type: string
  section_or_article: string
  excerpt: string
  source_url?: string | null
  verification_status: 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'UNVERIFIED' | 'CONFLICTING'
}

export interface ABSMissingInfo {
  field_name: string
  prompt_question: string
  impact_description: string
  why_it_matters: string
}

export interface ABSHumanEscalation {
  human_review: boolean
  reason?: string | null
  missing_information?: string[]
  case_summary?: string | null
  triggered_rules?: string[]
  sources?: string[]
}

export interface ABSAssessResponse {
  status?: ABSStatus
  pathway?: string
  relevance: ABSRelevance
  reasoning: string[]
  applicable_authority_guidance: string[]
  ip_filing_flag: boolean
  ip_filing_note?: string | null
  facts_considered?: Record<string, any>
  triggered_rules?: ABSTriggeredRule[]
  exemptions_evaluated?: ABSExemptionCheck[]
  authority_routing?: ABSAuthorityRouting
  form_requirements?: ABSFormRequirement[]
  benefit_sharing?: BenefitSharingProfile
  certificate_of_origin?: CertificateOfOriginProfile
  citations?: ABSCitation[]
  missing_information?: ABSMissingInfo[]
  next_actions?: string[]
  human_escalation?: ABSHumanEscalation
  abstained?: boolean
  abstain_reason?: string | null
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
