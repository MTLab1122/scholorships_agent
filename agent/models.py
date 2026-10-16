"""Data models for Scholarship Research & Verification Agent.
Implements the required fields from Section 7, flags from Section 5, and runtime status fields.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


SponsorType = Literal[
    "federal govt",
    "provincial govt",
    "university",
    "NGO-foundation",
    "corporate",
    "international",
    "other",
    "not stated",
]

UniversityTypes = Literal[
    "public",
    "private",
    "both",
    "not stated",
]

EligibilityStatus = Literal[
    "yes",
    "no",
    "not stated",
]

OpportunityStatus = Literal[
    "Closing soon",
    "Open",
    "Upcoming",
    "Rolling / ongoing",
    "Deadline not stated",
    "Closed",
    "Previous cycle – awaiting new call",
]

LinkStatus = Literal[
    "working",
    "broken",
    "unreachable",
    "not stated",
]


class ScholarshipExtractionItem(BaseModel):
    """Schema for LLM structured extraction per individual scholarship opportunity."""
    name: str = Field(description="Exact scholarship name as written on page.")
    sponsor: str = Field(description="Entity funding or offering the award.")
    sponsor_type: SponsorType = Field(
        default="other",
        description="One of: federal govt, provincial govt, university, NGO-foundation, corporate, international, other, not stated."
    )
    university_types: UniversityTypes = Field(
        default="not stated",
        description="One of: public, private, both, not stated."
    )
    eligible_institutions: str = Field(
        default="not stated",
        description="Universities or institutions eligible, or 'not stated'."
    )
    degree_levels: str = Field(
        default="not stated",
        description="e.g. Undergraduate, Master's, PhD, Intermediate, or 'not stated'."
    )
    fields_of_study: str = Field(
        default="not stated",
        description="Fields of study or faculties covered, or 'not stated'."
    )
    academic_years: str = Field(
        default="not stated",
        description="e.g. 1st year students only, all years, or 'not stated'."
    )
    domicile_requirements: str = Field(
        default="not stated",
        description="Domicile requirements copied verbatim, or 'not stated'."
    )
    district_requirements: str = Field(
        default="not stated",
        description="Specific districts if any, or 'not stated'."
    )
    other_geographic: str = Field(
        default="not stated",
        description="Tehsils, union councils, operational areas, or 'not stated'."
    )
    kp_eligibility: EligibilityStatus = Field(
        default="not stated",
        description="yes, no, or not stated."
    )
    charsadda_eligibility: EligibilityStatus = Field(
        default="not stated",
        description="yes, no, or not stated."
    )
    merit_criteria: str = Field(
        default="not stated",
        description="Merit conditions, test score, or 'not stated'."
    )
    need_criteria: str = Field(
        default="not stated",
        description="Financial need conditions, or 'not stated'."
    )
    min_gpa_or_marks: str = Field(
        default="not stated",
        description="Minimum GPA or percentage marks threshold copied verbatim, or 'not stated'."
    )
    income_cap: str = Field(
        default="not stated",
        description="Maximum monthly/annual family income ceiling with currency, or 'not stated'."
    )
    age_limit: str = Field(
        default="not stated",
        description="Age limit condition, or 'not stated'."
    )
    gender: str = Field(
        default="not stated",
        description="Female only, male only, all, or 'not stated'."
    )
    other_conditions: str = Field(
        default="not stated",
        description="Other rules or exclusions, or 'not stated'."
    )
    award_amount: str = Field(
        default="not stated",
        description="Rupee or foreign currency amount as written, or 'not stated'."
    )
    benefits: str = Field(
        default="not stated",
        description="Tuition fee waiver, monthly stipend, hostel, books, travel, or 'not stated'."
    )
    duration: str = Field(
        default="not stated",
        description="Duration of award (e.g. 1 year, 4 years degree), or 'not stated'."
    )
    number_of_awards: str = Field(
        default="not stated",
        description="Total slots available, or 'not stated'."
    )
    application_procedure: str = Field(
        default="not stated",
        description="Online portal, university SFAO, mail, etc., or 'not stated'."
    )
    required_documents: str = Field(
        default="not stated",
        description="CNIC, domicile, salary slips, utility bills, transcripts, etc., or 'not stated'."
    )
    attestation_requirements: str = Field(
        default="not stated",
        description="Attestation by Gazetted officer, Notary, etc., or 'not stated'."
    )
    apply_url: str = Field(
        default="not stated",
        description="Direct application link (absolute URL) or 'not stated'."
    )
    opening_date: str = Field(
        default="not stated",
        description="Opening date as YYYY-MM-DD or original text if partial, or 'not stated'."
    )
    deadline: str = Field(
        default="not stated",
        description="Closing date as YYYY-MM-DD or original text if partial, or 'not stated'."
    )
    document_upload_deadline: str = Field(
        default="not stated",
        description="Hardcopy/document upload deadline if distinct, or 'not stated'."
    )
    expiry_date: str = Field(
        default="not stated",
        description="Expiry date of call if stated, or 'not stated'."
    )
    cycle: str = Field(
        default="not stated",
        description="Academic year or session (e.g. 2026-27, Fall 2026), or 'not stated'."
    )
    contact_email: str = Field(default="not stated")
    contact_phone: str = Field(default="not stated")
    contact_address: str = Field(default="not stated")
    source_url: str = Field(default="not stated")
    evidence_quote: str = Field(
        default="not stated",
        description="Verbatim excerpt up to 300 characters from page proving eligibility/deadline."
    )
    confirmed_by_official_source: bool = Field(
        default=False,
        description="True only if source tier is 1 or 2 and values appear on the page."
    )


class ExtractionResponse(BaseModel):
    """Container for LLM extraction response."""
    scholarships: List[ScholarshipExtractionItem] = Field(default_factory=list)


class ScholarshipRecord(ScholarshipExtractionItem):
    """Full scholarship record including runtime verification, flags, and retention fields."""
    id: str = Field(default="", description="Unique normalized record ID")
    
    # Priority flags (Section 5)
    charsadda_flag: bool = Field(
        default=False,
        description="Charsadda named explicitly, district/zone includes Charsadda, or reserved for BKUC."
    )
    kp_flag: bool = Field(
        default=False,
        description="KP domicile explicitly required/favored, or KP-wide programme."
    )
    pakistan_wide_kp_eligible: bool = Field(
        default=False,
        description="Open to all Pakistan and KP is not excluded."
    )
    target_uni_flag: bool = Field(
        default=False,
        description="Names UoP, UET Peshawar, or Abasyn University."
    )
    merged_districts_only: bool = Field(
        default=False,
        description="Limited to ex-FATA merged districts. Never sets charsadda_flag."
    )

    # Runtime status and verification
    status: OpportunityStatus = Field(default="Deadline not stated")
    days_left: Optional[int] = Field(default=None)
    source_trust_tier: int = Field(default=1, description="1=Official, 2=Official secondary, 3=Unofficial")
    verification_badge: str = Field(default="Unverified") # "Confirmed", "Via Partner", "Unverified"
    claimed_by_source: Optional[str] = Field(default=None)

    # Link verification
    link_status_apply: LinkStatus = Field(default="not stated")
    link_status_source: LinkStatus = Field(default="not stated")
    
    # Audit & retention
    first_seen: str = Field(default="", description="YYYY-MM-DD date first discovered")
    last_verified: str = Field(default="", description="YYYY-MM-DD date last verified against page")
    is_reconfirmed_today: bool = Field(default=True)
    all_source_urls: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)


class DiscoveryItem(BaseModel):
    """Candidate item discovered during search phase."""
    name: str
    sponsor: str
    official_url: str = ""
    other_url: str = ""
    deadline_claim: str = "not stated"
    why_relevant: str = ""


class ReportSummary(BaseModel):
    """Summary counts for daily report header."""
    title: str
    audience: str
    generated_at_pkt: str
    run_id: str
    sources_checked_count: int
    total_opportunities: int
    new_since_yesterday: int
    closing_within_7_days: int
    charsadda_eligible_count: int
    kp_eligible_count: int
    broken_links_count: int
    degraded_mode: bool = False
