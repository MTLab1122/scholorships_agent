"""Gemini API client wrapper using google-genai SDK.
Handles:
- gemini-3.8-flash primary model with gemini-3.5-flash-lite fallback
- Exponential backoff retries (3 attempts)
- Structured JSON output for scholarship extraction
- Google Search grounding for discovery queries
- Graceful mock fallback for testing without API keys
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from agent.models import ExtractionResponse, ScholarshipExtractionItem, DiscoveryItem
from agent.prompts import SYSTEM_PROMPT, DISCOVERY_PROMPT, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class GeminiScholarshipClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: str = "gemini-3.8-flash",
        fallback_model: str = "gemini-3.5-flash-lite",
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI Client: {e}")

    def run_discovery_query(
        self,
        query: str,
        focus: str,
        today_pkt: str,
        cycle: str
    ) -> List[DiscoveryItem]:
        """Runs a search discovery query through Gemini with Google Search tool."""
        prompt = DISCOVERY_PROMPT.format(
            today=today_pkt,
            cycle=cycle,
            focus=focus
        )
        user_message = f"{prompt}\nQuery focus: {query}"

        if not self.client:
            logger.info(f"No Gemini API key available. Running discovery in mock mode for focus: {focus}")
            return self._mock_discovery(focus, query)

        def _call_model(model_name: str):
            # Using search grounding tool
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            )
            resp = self.client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=config
            )
            return resp

        resp = self._execute_with_retry(_call_model)
        if not resp or not resp.text:
            return []

        # Parse JSON array from model output
        return self._parse_discovery_json(resp.text)

    def extract_scholarships_from_page(
        self,
        page_text: str,
        source_url: str,
        tier: int,
        links_map: Dict[str, str],
        today_pkt: str,
        cycle: str
    ) -> List[ScholarshipExtractionItem]:
        """Extracts structured scholarship opportunities from page text."""
        # Format links list for prompt (up to 50 links)
        formatted_links = "\n".join(
            f"{text} → {url}"
            for text, url in list(links_map.items())[:50]
        ) or "None provided"

        prompt = EXTRACTION_PROMPT.format(
            today=today_pkt,
            url=source_url,
            tier=tier,
            links=formatted_links,
            cycle=cycle,
            page_text=page_text[:40000] # Ensure within context limits
        )

        if not self.client:
            logger.info(f"No Gemini API key available. Mock extracting from {source_url}")
            return self._mock_extraction(source_url, tier, cycle)

        def _call_model(model_name: str):
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=ExtractionResponse.model_json_schema(),
                temperature=0.1,
            )
            resp = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return resp

        resp = self._execute_with_retry(_call_model)
        if not resp or not resp.text:
            return []

        try:
            parsed = ExtractionResponse.model_validate_json(resp.text)
            return parsed.scholarships
        except Exception as e:
            logger.warning(f"Error validating structured output JSON: {e}. Output text preview: {resp.text[:300]}")
            # Fallback parsing
            try:
                data = json.loads(resp.text)
                if isinstance(data, dict) and "scholarships" in data:
                    return [ScholarshipExtractionItem(**item) for item in data["scholarships"]]
                elif isinstance(data, list):
                    return [ScholarshipExtractionItem(**item) for item in data]
            except Exception as e2:
                logger.error(f"Fallback JSON parsing also failed: {e2}")
            return []

    def _execute_with_retry(self, call_func):
        """Executes API call with exponential backoff and fallback model switch."""
        for attempt in range(1, self.max_retries + 1):
            try:
                return call_func(self.primary_model)
            except Exception as e:
                logger.warning(f"Primary model {self.primary_model} attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor ** attempt
                    time.sleep(sleep_time)

        # Fallback to secondary model
        logger.warning(f"Switching to fallback model: {self.fallback_model}")
        try:
            return call_func(self.fallback_model)
        except Exception as e:
            logger.error(f"Fallback model {self.fallback_model} also failed: {e}")
            return None

    def _parse_discovery_json(self, text: str) -> List[DiscoveryItem]:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            raw_items = json.loads(cleaned)
            if isinstance(raw_items, list):
                return [DiscoveryItem(**item) for item in raw_items if isinstance(item, dict)]
        except Exception as e:
            logger.warning(f"Failed to parse discovery JSON: {e}")
        return []

    def _mock_discovery(self, focus: str, query: str) -> List[DiscoveryItem]:
        """Provides realistic mock discovery items for testing without an API key."""
        return [
            DiscoveryItem(
                name="HEC Need Based Scholarships Programme 2026-27",
                sponsor="Higher Education Commission Pakistan",
                official_url="https://www.hec.gov.pk/english/scholarshipsgrants/NBS/Pages/default.aspx",
                other_url="",
                deadline_claim="2026-11-30",
                why_relevant="Federal need-based scholarship covering full tuition and stipend for KP public university students"
            ),
            DiscoveryItem(
                name="Bacha Khan University Charsadda Need-cum-Merit Scholarship",
                sponsor="Bacha Khan University Charsadda",
                official_url="https://bkuc.edu.pk/financial-aid",
                other_url="",
                deadline_claim="2026-10-31",
                why_relevant="Special aid for enrolled students of Bacha Khan University Charsadda"
            ),
            DiscoveryItem(
                name="KP Education Foundation (KPEF) Higher Education Scholarship",
                sponsor="KP Education Foundation",
                official_url="https://ef.kp.gov.pk/",
                other_url="",
                deadline_claim="2026-12-15",
                why_relevant="KP provincial government scholarship for KP domicile students"
            ),
            DiscoveryItem(
                name="Ihsan Trust Qarz-e-Hasna Interest-Free Student Loan",
                sponsor="Ihsan Trust",
                official_url="https://www.ihsantrust.org/education-loan/",
                other_url="",
                deadline_claim="Rolling / ongoing",
                why_relevant="Interest-free repayment facility for students unable to afford university fees"
            ),
            DiscoveryItem(
                name="Abasyn University Peshawar Financial Assistance 2026",
                sponsor="Abasyn University Peshawar",
                official_url="https://abasyn.edu.pk/scholarships/",
                other_url="",
                deadline_claim="2026-11-15",
                why_relevant="Tuition fee waivers for private university students in Peshawar"
            )
        ]

    def _mock_extraction(self, source_url: str, tier: int, cycle: str) -> List[ScholarshipExtractionItem]:
        """Returns realistic structured items when extracting without active API key."""
        low_url = source_url.lower()

        if "bkuc" in low_url or "charsadda" in low_url:
            return [
                ScholarshipExtractionItem(
                    name="Bacha Khan University Charsadda Deserving Student Support Fund",
                    sponsor="Bacha Khan University Charsadda (BKUC)",
                    sponsor_type="university",
                    university_types="public",
                    eligible_institutions="Bacha Khan University Charsadda",
                    degree_levels="Undergraduate, Master's",
                    fields_of_study="All regular departments",
                    academic_years="All enrolled academic years",
                    domicile_requirements="Charsadda district domicile preferred; open to all KP domicile students",
                    district_requirements="Charsadda",
                    other_geographic="Settled district Charsadda",
                    kp_eligibility="yes",
                    charsadda_eligibility="yes",
                    merit_criteria="Minimum 2.50 CGPA or 50% marks in previous examination",
                    need_criteria="Low family income with priority to orphans and daily-wage dependents",
                    min_gpa_or_marks="2.50 CGPA",
                    income_cap="PKR 45,000 per month",
                    age_limit="not stated",
                    gender="all",
                    other_conditions="Must not be receiving any other government or private scholarship simultaneously",
                    award_amount="Up to 100% tuition fee waiver plus PKR 3,000 monthly stipend",
                    benefits="Tuition waiver and semester stipend",
                    duration="One academic semester, renewable based on academic standing",
                    number_of_awards="150 awards per cycle",
                    application_procedure="Submit prescribed financial aid form to Students Financial Aid Office (SFAO) BKUC",
                    required_documents="CNIC/B-Form copy, Father's death/salary certificate, last semester transcript, utility bill copies",
                    attestation_requirements="Attested by Gazetted Officer or Village Council Chairman",
                    apply_url="https://bkuc.edu.pk/financial-aid/apply",
                    opening_date="2026-10-01",
                    deadline="2026-10-31",
                    document_upload_deadline="2026-11-05",
                    expiry_date="2026-11-05",
                    cycle=cycle,
                    contact_email="sfao@bkuc.edu.pk",
                    contact_phone="+92-91-6540064",
                    contact_address="Students Financial Aid Office, Bacha Khan University Charsadda, Khyber Pakhtunkhwa",
                    source_url=source_url,
                    evidence_quote="Applications are invited from deserving students of BKUC for Need-cum-Merit Financial Aid. Special consideration for Charsadda district domicile holders.",
                    confirmed_by_official_source=(tier in [1, 2])
                )
            ]
        elif "hec" in low_url:
            return [
                ScholarshipExtractionItem(
                    name="HEC Need Based Scholarship Programme 2026-27",
                    sponsor="Higher Education Commission (HEC) Pakistan",
                    sponsor_type="federal govt",
                    university_types="public",
                    eligible_institutions="All HEC-recognized public sector universities in Pakistan including UoP, UET Peshawar, BKUC, KMU, AUP, AWKUM",
                    degree_levels="Undergraduate (4-5 years)",
                    fields_of_study="All disciplines",
                    academic_years="1st and 2nd semester enrolled students",
                    domicile_requirements="All Pakistan including Khyber Pakhtunkhwa",
                    district_requirements="not stated",
                    other_geographic="All KP districts including Charsadda",
                    kp_eligibility="yes",
                    charsadda_eligibility="yes",
                    merit_criteria="Enrolled in regular program with satisfactory academic progress",
                    need_criteria="Financially disadvantaged students from rural and underprivileged backgrounds",
                    min_gpa_or_marks="not stated",
                    income_cap="PKR 45,000 per month family income",
                    age_limit="not stated",
                    gender="all",
                    other_conditions="Full-time enrolled student in partner public sector universities",
                    award_amount="Full tuition fee coverage plus PKR 6,000 monthly living allowance",
                    benefits="100% tuition fee waiver, monthly stipend, book allowance",
                    duration="Complete duration of degree program",
                    number_of_awards="Over 10,000 slots nationally",
                    application_procedure="Apply online via HEC portal and submit verified hardcopy to University SFAO",
                    required_documents="Salary slip or income certificate, CNIC of applicant and father, electricity bills (last 6 months), educational transcripts",
                    attestation_requirements="Income certificate attested by relevant Revenue Authority / Tehsildar",
                    apply_url="https://ehsaas.hec.gov.pk/",
                    opening_date="2026-09-15",
                    deadline="2026-11-30",
                    document_upload_deadline="2026-12-07",
                    expiry_date="2026-12-07",
                    cycle=cycle,
                    contact_email="financial-aid@hec.gov.pk",
                    contact_phone="+92-51-111-119-432",
                    contact_address="HEC Secretariat, Sector H-9, Islamabad",
                    source_url=source_url,
                    evidence_quote="HEC Need Based Scholarships provide complete tuition and monthly stipends for deserving undergraduate students in public universities across Pakistan including Khyber Pakhtunkhwa.",
                    confirmed_by_official_source=(tier in [1, 2])
                )
            ]
        elif "abasyn" in low_url:
            return [
                ScholarshipExtractionItem(
                    name="Abasyn University Peshawar Merit & Need-Based Scholarship",
                    sponsor="Abasyn University Peshawar",
                    sponsor_type="university",
                    university_types="private",
                    eligible_institutions="Abasyn University Peshawar Campus",
                    degree_levels="Undergraduate, Master's",
                    fields_of_study="Computer Science, Software Engineering, Pharmacy, Engineering, Management Sciences",
                    academic_years="All semesters",
                    domicile_requirements="KP and other provinces",
                    district_requirements="not stated",
                    other_geographic="Peshawar, Charsadda, Nowshera",
                    kp_eligibility="yes",
                    charsadda_eligibility="yes",
                    merit_criteria="Above 3.00 CGPA or 70% marks for merit scholarships",
                    need_criteria="Documented hardship or low family earnings",
                    min_gpa_or_marks="3.00 CGPA",
                    income_cap="PKR 60,000 per month",
                    age_limit="not stated",
                    gender="all",
                    other_conditions="Continuous satisfactory attendance (minimum 80%)",
                    award_amount="25% to 100% tuition fee discount",
                    benefits="Tuition waiver",
                    duration="Semester-by-semester renewal",
                    number_of_awards="300 awards per session",
                    application_procedure="Submit form to Abasyn Admissions & Financial Aid Office",
                    required_documents="Income proof, academic certificates, CNIC copies",
                    attestation_requirements="not stated",
                    apply_url="https://abasyn.edu.pk/scholarships/apply",
                    opening_date="2026-10-05",
                    deadline="2026-11-15",
                    document_upload_deadline="2026-11-20",
                    expiry_date="2026-11-20",
                    cycle=cycle,
                    contact_email="admissions@abasyn.edu.pk",
                    contact_phone="+92-91-2582835",
                    contact_address="Ring Road (Charsadda Link Road), Peshawar, Khyber Pakhtunkhwa",
                    source_url=source_url,
                    evidence_quote="Abasyn University provides substantial need and merit scholarships up to 100% tuition fee waiver for undergraduate and graduate students in Peshawar.",
                    confirmed_by_official_source=(tier in [1, 2])
                )
            ]
        elif "ihsan" in low_url:
            return [
                ScholarshipExtractionItem(
                    name="Ihsan Trust Qarz-e-Hasna Facility for Higher Education",
                    sponsor="Ihsan Trust",
                    sponsor_type="NGO-foundation",
                    university_types="both",
                    eligible_institutions="Over 150 partner universities including public and private universities in KP",
                    degree_levels="Undergraduate, Postgraduate",
                    fields_of_study="All professional disciplines",
                    academic_years="All academic years",
                    domicile_requirements="Open to all Pakistani citizens including KP and Charsadda",
                    district_requirements="not stated",
                    other_geographic="All Pakistan",
                    kp_eligibility="yes",
                    charsadda_eligibility="yes",
                    merit_criteria="Good academic performance with minimum 2.50 CGPA",
                    need_criteria="Purely need-based for students unable to pay educational expenses",
                    min_gpa_or_marks="2.50 CGPA",
                    income_cap="not stated",
                    age_limit="not stated",
                    gender="all",
                    other_conditions="Pure interest-free loan (Qarz-e-Hasna) repayable in nominal installments after completion of degree and employment",
                    award_amount="100% tuition fee loan paid directly to the university",
                    benefits="Pure interest-free educational loan, zero markup, flexible post-graduation repayment",
                    duration="Duration of degree program",
                    number_of_awards="Unlimited for eligible candidates",
                    application_procedure="Apply online via Ihsan Trust portal or university financial aid office",
                    required_documents="University fee voucher, salary slip/income affidavit, CNIC, academic transcripts",
                    attestation_requirements="Income affidavit on PKR 100 stamp paper",
                    apply_url="https://www.ihsantrust.org/apply-now/",
                    opening_date="Rolling / ongoing",
                    deadline="Rolling / ongoing",
                    document_upload_deadline="not stated",
                    expiry_date="not stated",
                    cycle=cycle,
                    contact_email="info@ihsantrust.org",
                    contact_phone="+92-21-34315481",
                    contact_address="Ihsan Trust, Karachi, Pakistan",
                    source_url=source_url,
                    evidence_quote="Ihsan Trust provides purely interest-free student loans (Qarz-e-Hasna) for needy students across all partner public and private universities in Pakistan.",
                    confirmed_by_official_source=(tier in [1, 2])
                )
            ]
        elif "chevening" in low_url or "fulbright" in low_url:
            return [
                ScholarshipExtractionItem(
                    name="Chevening Pakistan Scholarships 2026-27",
                    sponsor="UK Foreign, Commonwealth and Development Office (FCDO)",
                    sponsor_type="international",
                    university_types="both",
                    eligible_institutions="All accredited UK Universities",
                    degree_levels="One-year taught Master's degree",
                    fields_of_study="All subjects",
                    academic_years="Graduating seniors / graduates with 2 years work experience",
                    domicile_requirements="Citizen of Pakistan (including KP and Charsadda)",
                    district_requirements="not stated",
                    other_geographic="Pakistan-wide",
                    kp_eligibility="yes",
                    charsadda_eligibility="yes",
                    merit_criteria="Undergraduate degree equivalent to UK upper second-class 2:1 honours",
                    need_criteria="not stated",
                    min_gpa_or_marks="3.00 CGPA or equivalent",
                    income_cap="not stated",
                    age_limit="not stated",
                    gender="all",
                    other_conditions="Minimum two years (2,800 hours) of work experience and commitment to return to Pakistan for at least two years",
                    award_amount="Fully funded: University tuition fees, monthly living stipend, return economy flights, arrival allowance",
                    benefits="100% tuition, monthly allowance, visa, flights",
                    duration="1 year",
                    number_of_awards="Approximately 50-60 from Pakistan annually",
                    application_procedure="Online application via Chevening central portal",
                    required_documents="Passport, academic transcripts, two reference letters, leadership and career essays",
                    attestation_requirements="Official attested university degrees",
                    apply_url="https://www.chevening.org/scholarship/pakistan/",
                    opening_date="2026-08-05",
                    deadline="2026-11-05",
                    document_upload_deadline="2026-11-05",
                    expiry_date="2026-11-05",
                    cycle=cycle,
                    contact_email="chevening.pakistan@fcdo.gov.uk",
                    contact_phone="not stated",
                    contact_address="British High Commission, Islamabad",
                    source_url=source_url,
                    evidence_quote="Chevening Scholarships enable outstanding emerging leaders from Pakistan, including Khyber Pakhtunkhwa, to pursue one-year master's degrees in the UK on full funding.",
                    confirmed_by_official_source=(tier in [1, 2])
                )
            ]
        else:
            return []
