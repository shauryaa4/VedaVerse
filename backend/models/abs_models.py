"""
ABS Data Models — Production Access and Benefit Sharing Engine Models.

Defines structured models for applicant entity, biological resource, access source,
traditional knowledge, activity profile, IPR lifecycle, exemptions, authority routing,
form routing, benefit-sharing calculations, citation verification, abstention, and human escalation.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

# --- Enums & Literals ---
EntityCategory = Literal[
    "indian_citizen",
    "indian_company_no_foreign_control",
    "indian_company_with_foreign_control",
    "foreign_entity_or_individual",
    "ayush_practitioner",
    "unknown",
]

ApplicantType = Literal[
    "individual",
    "company",
    "research_institution",
    "trust_society",
    "other",
    "unknown",
]

ResourceType = Literal[
    "plant",
    "animal",
    "microbial",
    "other_biological",
    "non_biological",
    "unknown",
]

OriginStatus = Literal["india", "foreign", "unknown"]

AccessMethod = Literal[
    "direct_field_collection",
    "trader_market",
    "cultivator",
    "repository_institution",
    "other",
    "unknown",
]

SourceType = Literal[
    "cultivated",
    "wild_collected",
    "artificially_propagated",
    "market_or_trader",
    "supplier",
    "community",
    "institution",
    "unknown",
]

TKType = Literal["none", "codified", "community", "both", "unknown"]

ActivityType = Literal[
    "research",
    "bio_survey",
    "bio_utilisation",
    "commercial_utilisation",
    "resource_transfer",
    "research_result_transfer",
    "ipr_application",
    "ipr_grant",
    "ipr_commercialisation",
    "other",
]

IPRStage = Literal[
    "NO_IPR",
    "CONSIDERING_IPR",
    "PREPARING_APPLICATION",
    "IPR_APPLICATION",
    "IPR_GRANTED",
    "IPR_COMMERCIALISATION",
    "UNKNOWN",
]

CertificateStatus = Literal["REQUIRED", "PROVIDED", "MISSING", "NOT_APPLICABLE"]

TransferType = Literal[
    "biological_resource",
    "research_results",
    "traditional_knowledge",
    "IPR",
    "other",
]

EvidenceStatus = Literal[
    "STRONG",
    "CONDITIONAL",
    "INSUFFICIENT_INFORMATION",
    "CONFLICTING",
    "ESCALATION_RECOMMENDED",
]

CitationVerificationStatus = Literal[
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTING",
]

ABSRelevance = Literal["likely", "possible", "unlikely", "not_applicable"]


FactKnowledgeState = Literal["KNOWN", "UNKNOWN", "AMBIGUOUS", "CONFLICTING"]


# --- Fact Components ---

class ApplicantEntityProfile(BaseModel):
    entity_category: EntityCategory = "unknown"
    applicant_type: ApplicantType = "unknown"
    nationality: Optional[str] = None
    incorporation_country: Optional[str] = None
    foreign_participation_or_control: Optional[bool] = None
    status: FactKnowledgeState = "UNKNOWN"


class BiologicalResourceProfile(BaseModel):
    biological_resource_involved: bool = False
    resource_name: Optional[str] = None
    scientific_name: Optional[str] = None
    resource_type: ResourceType = "unknown"
    resource_part: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    country_of_origin: Optional[str] = None
    origin_status: OriginStatus = "unknown"
    geographical_location: Optional[str] = None
    status: FactKnowledgeState = "UNKNOWN"


class AccessSourceProfile(BaseModel):
    access_method: AccessMethod = "unknown"
    source_type: SourceType = "unknown"
    cultivated: bool = False
    wild_collected: bool = False
    artificially_propagated: bool = False
    market_or_trader: bool = False
    supplier: Optional[str] = None
    community: Optional[str] = None
    institution: Optional[str] = None
    repository_location: Optional[str] = None
    status: FactKnowledgeState = "UNKNOWN"


class TraditionalKnowledgeProfile(BaseModel):
    associated_traditional_knowledge: bool = False
    tk_type: TKType = "none"
    tk_source: Optional[str] = None
    tk_codified: bool = False
    tk_community_based: bool = False
    status: FactKnowledgeState = "UNKNOWN"


class ActivityProfile(BaseModel):
    activities: list[ActivityType] = Field(default_factory=list)
    status: FactKnowledgeState = "UNKNOWN"


class IPRLifecycleProfile(BaseModel):
    ipr_stage: IPRStage = "UNKNOWN"
    ipr_type: Optional[str] = "patent"
    jurisdiction_filed: Optional[str] = None
    status: FactKnowledgeState = "UNKNOWN"


class CertificateOfOriginProfile(BaseModel):
    certificate_required: bool = False
    certificate_available: bool = False
    certificate_status: CertificateStatus = "NOT_APPLICABLE"
    issuing_authority: Optional[str] = None
    note: Optional[str] = None


class TransferProfile(BaseModel):
    transfer_involved: bool = False
    transfer_type: Optional[TransferType] = None
    transferee_type: Optional[str] = None
    transferee_country: Optional[str] = None


class ABSFactProfile(BaseModel):
    """Structured facts specific to ABS decision support."""
    applicant: ApplicantEntityProfile = Field(default_factory=ApplicantEntityProfile)
    resource: BiologicalResourceProfile = Field(default_factory=BiologicalResourceProfile)
    access: AccessSourceProfile = Field(default_factory=AccessSourceProfile)
    tk: TraditionalKnowledgeProfile = Field(default_factory=TraditionalKnowledgeProfile)
    activity: ActivityProfile = Field(default_factory=ActivityProfile)
    ipr: IPRLifecycleProfile = Field(default_factory=IPRLifecycleProfile)
    certificate_of_origin: CertificateOfOriginProfile = Field(default_factory=CertificateOfOriginProfile)
    transfer: TransferProfile = Field(default_factory=TransferProfile)
    annual_turnover_inr: Optional[float] = None
    is_itpgrfa_crop: bool = False
    government_approved_collaboration: bool = False


# --- Engine Outputs ---

class ABSTriggeredRule(BaseModel):
    rule_id: str
    rule_name: str
    section_or_rule: str
    description: str
    authority: str
    required_form: Optional[str] = None
    source_doc_id: str
    source_provision: str
    effective_date: Optional[str] = None
    source_url: Optional[str] = None


class ABSExemptionCheck(BaseModel):
    exemption_id: str
    name: str
    source_provision: str
    conditions_checked: dict[str, Any] = Field(default_factory=dict)
    is_triggered: bool = False
    reason: str
    source_doc_id: str
    effective_date: Optional[str] = None
    source_url: Optional[str] = None


class ABSFormRequirement(BaseModel):
    form_id: str
    form_name: str
    purpose: str
    authority: str
    fee: str
    required_documents: list[str] = Field(default_factory=list)
    source_doc_id: str
    source_url: Optional[str] = None


class ABSAuthorityRouting(BaseModel):
    authority_name: str
    authority_level: str
    jurisdiction_scope: str
    reasons: list[str] = Field(default_factory=list)
    status: str = "DETERMINED"  # DETERMINED or INSUFFICIENT_INFORMATION


class BenefitSharingProfile(BaseModel):
    applicable: bool = False
    basis: Optional[str] = None
    benefit_type: Optional[str] = None
    turnover_inr: Optional[float] = None
    turnover_band: Optional[str] = None
    rate_or_slab: Optional[str] = None
    indicative_amount_inr: Optional[float] = None
    special_condition: Optional[str] = None
    calculation_status: str = "NOT_CALCULATED"
    disclaimer: str = (
        "Indicative calculation based on Biological Diversity Rules 2024 benefit sharing guidelines. "
        "Final benefit sharing obligations are determined solely by NBA/SBB during formal agreement execution."
    )
    source: Optional[str] = None


class ABSCitation(BaseModel):
    doc_id: str
    document_name: str
    document_type: str
    section_or_article: str
    excerpt: str
    source_url: Optional[str] = None
    verification_status: CitationVerificationStatus = "UNVERIFIED"
    source_id: Optional[str] = None
    source_title: Optional[str] = None
    authority: Optional[str] = None
    effective_date: Optional[str] = None


class ABSMissingInfo(BaseModel):
    field_name: str
    prompt_question: str
    impact_description: str
    why_it_matters: str


class ABSHumanEscalation(BaseModel):
    human_review: bool = False
    reason: Optional[str] = None
    missing_information: list[str] = Field(default_factory=list)
    case_summary: Optional[str] = None
    triggered_rules: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)
    missing_facts: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class ABSGroundedCitation(BaseModel):
    """
    ABS-03 (from main) - links one line of ABSAssessment.reasoning to the corpus
    chunk retrieved from the shared biodiversity_abs Chroma collection and scored
    with citation_verification.score_overlap. verified=False is a normal outcome
    (caveat lines, or no strong-matching chunk) - not an error.
    Kept separate from ABSCitation (the engine's manifest-based citation).
    """

    reasoning_text: str
    doc_id: Optional[str] = None
    document_name: Optional[str] = None
    section_or_article: Optional[str] = None
    source_url: Optional[str] = None
    excerpt: Optional[str] = None
    verified: bool = False


class ABSAssessment(BaseModel):
    """The ABS-aware decision-support read-out for one Product Intelligence Profile."""

    # Core status & pathway
    status: EvidenceStatus = "CONDITIONAL"
    pathway: str = "UNRESOLVED"

    # Backward-compatible fields
    relevance: ABSRelevance = "possible"
    reasoning: list[str] = Field(default_factory=list)
    applicable_authority_guidance: list[str] = Field(default_factory=list)
    ip_filing_flag: bool = False
    ip_filing_note: Optional[str] = None

    # Fact breakdown
    facts_considered: dict[str, Any] = Field(default_factory=dict)

    # Detailed legal engine analysis
    triggered_rules: list[ABSTriggeredRule] = Field(default_factory=list)
    exemptions_evaluated: list[ABSExemptionCheck] = Field(default_factory=list)
    authority_routing: Optional[ABSAuthorityRouting] = None
    form_requirements: list[ABSFormRequirement] = Field(default_factory=list)
    benefit_sharing: BenefitSharingProfile = Field(default_factory=BenefitSharingProfile)
    certificate_of_origin: CertificateOfOriginProfile = Field(default_factory=CertificateOfOriginProfile)
    citations: list[ABSCitation] = Field(default_factory=list)
    missing_information: list[ABSMissingInfo] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    human_escalation: ABSHumanEscalation = Field(default_factory=ABSHumanEscalation)

    abstained: bool = False
    abstain_reason: Optional[str] = None

    disclaimer: str = (
        "ABS-aware decision support — DEMO HELPER, not a compliance filing "
        "determination. Based on a deterministic legal pathway engine reading of India's "
        "Biological Diversity Act, 2002 (as amended by Act 10 of 2023, with Rules notified in 2024) "
        "applied to the structured product information provided. This tool is NOT connected to the "
        "National Biodiversity Authority, any State Biodiversity Board, or any government system — "
        "verify against current NBA-notified guidelines and consult a qualified ABS/IP professional "
        "before taking compliance action."
    )

    # ABS-03: populated by logic.abs_helper.ground_abs_citations() (optional post-step).
    grounded_reasoning: list[ABSGroundedCitation] = Field(default_factory=list)
