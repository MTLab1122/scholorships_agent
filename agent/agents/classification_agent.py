"""Agent 3: Classification Agent.
Classifies opportunities across the 11 primary categories and applies
grounded secondary labels (national/international, paid/unpaid, remote/onsite,
funding type, eligible semester ranges, and university sector).
"""

import re
import logging
from typing import Dict, Any, List, Optional
from agent.classifier import UniversityClassifier
from agent.models import ScholarshipRecord

logger = logging.getLogger(__name__)

PRIMARY_CATEGORIES = [
    "scholarships",
    "internships",
    "financial_aid",
    "research_fellowships",
    "competitions_hackathons",
    "conferences_exchange",
    "jobs_graduate_programs",
    "free_learning_certifications",
    "entrepreneurship_startups",
    "community_leadership",
    "fyp_industry_projects",
]


class OpportunityClassificationAgent:
    def __init__(self, university_classifier: Optional[UniversityClassifier] = None):
        self.uni_classifier = university_classifier or UniversityClassifier()

    def classify(self, record: ScholarshipRecord) -> ScholarshipRecord:
        """Alias for classify_record."""
        return self.classify_record(record)

    def classify_record(self, record: ScholarshipRecord) -> ScholarshipRecord:
        """Assigns primary category and secondary tags based on evidence in record."""
        text = f"{record.name} {record.sponsor} {record.benefits} {record.award_amount} {record.evidence_quote} {record.degree_levels}".lower()

        # 1. Primary Category
        record.category = self._determine_category(text, record)

        # 2. National vs. International
        sponsor_type = (record.sponsor_type or "").lower()
        if sponsor_type == "international" or any(kw in text for kw in ["overseas", "abroad", "foreign", "fulbright", "chevening", "daad", "commonwealth", "erasmus", "cern"]):
            record.is_international = True
            record.is_national = False
        else:
            record.is_national = True
            record.is_international = False

        # 3. Internships Work Mode & Paid Status
        if record.category in ["internships", "jobs_graduate_programs"]:
            if "remote" in text or "virtual" in text or "online" in text or "work from home" in text:
                record.work_mode = "remote"
            elif "hybrid" in text:
                record.work_mode = "hybrid"
            else:
                record.work_mode = "onsite"

            if any(kw in text for kw in ["unpaid", "volunteer", "no stipend"]):
                record.paid_status = "unpaid"
            elif any(kw in text for kw in ["paid", "stipend", "allowance", "pkr", "chf", "usd", "rs."]):
                record.paid_status = "paid"
            else:
                record.paid_status = "stipend"

        # 4. Funding attributes
        if any(kw in text for kw in ["fully funded", "full funding", "100%", "full tuition fee waiver"]):
            record.is_fully_funded = True
            record.is_partially_funded = False
        elif any(kw in text for kw in ["partial", "50%", "concession", "discount"]):
            record.is_partially_funded = True

        if any(kw in text for kw in ["need", "financial aid", "zakat", "income", "underprivileged", "deserving", "qarz"]):
            record.is_need_based = True
        if any(kw in text for kw in ["merit", "gpa", "marks", "test score", "hat", "gre", "top rank"]):
            record.is_merit_based = True

        # 5. Semester Eligibility Resolution
        record.eligible_semesters = self._resolve_semesters(text, record)

        # 6. University Sector Classification
        inst_text = f"{record.eligible_institutions} {record.sponsor} {record.name}"
        classified_sector = self.uni_classifier.classify_university_name(inst_text)
        if classified_sector != "not stated":
            record.university_types = classified_sector

        # 7. Priority Flags (Charsadda, KP, Target Unis)
        (
            record.charsadda_flag,
            record.kp_flag,
            record.pakistan_wide_kp_eligible,
            record.target_uni_flag,
            record.merged_districts_only
        ) = self.uni_classifier.calculate_priority_flags(record.model_dump())

        return record

    def _determine_category(self, text: str, record: ScholarshipRecord) -> str:
        """Determines best-fit primary category from opportunity text."""
        if any(kw in text for kw in ["internship", "intern", "trainee", "apprenticeship"]):
            return "internships"
        if any(kw in text for kw in ["hackathon", "competition", "coding contest", "challenge", "olympiad"]):
            return "competitions_hackathons"
        if any(kw in text for kw in ["research grant", "fellowship", "research assistant", "visiting researcher"]):
            return "research_fellowships"
        if any(kw in text for kw in ["conference", "student exchange", "summit", "ugrad", "youth forum"]):
            return "conferences_exchange"
        if any(kw in text for kw in ["job", "graduate trainee", "management trainee", "officer", "employment"]):
            return "jobs_graduate_programs"
        if any(kw in text for kw in ["free course", "certification", "voucher", "bootcamp", "training", "digiskills"]):
            return "free_learning_certifications"
        if any(kw in text for kw in ["incubator", "startup", "entrepreneur", "accelerator", "seed fund"]):
            return "entrepreneurship_startups"
        if any(kw in text for kw in ["volunteer", "community service", "leadership program", "youth activist"]):
            return "community_leadership"
        if any(kw in text for kw in ["final year project", "fyp", "ngiri", "capstone project", "project funding"]):
            return "fyp_industry_projects"
        if any(kw in text for kw in ["financial aid", "fee concession", "fee waiver", "emergency aid", "qarz"]):
            return "financial_aid"
        return "scholarships"

    def _resolve_semesters(self, text: str, record: ScholarshipRecord) -> List[int]:
        """Resolves specific semester numbers from criteria text."""
        semesters: List[int] = []

        # Explicit mentions like "1st semester", "semester 7 and 8", "3rd to 6th semester"
        if re.search(r"\b(1st|first)\s+semester\b", text) or "entry semester" in text or "newly admitted" in text:
            semesters.extend([1])
        if re.search(r"\b(2nd|second)\s+semester\b", text):
            semesters.append(2)
        if re.search(r"\b(3rd|third)\s+semester\b", text):
            semesters.append(3)
        if re.search(r"\b(4th|fourth)\s+semester\b", text):
            semesters.append(4)
        if re.search(r"\b(5th|fifth)\s+semester\b", text):
            semesters.append(5)
        if re.search(r"\b(6th|sixth)\s+semester\b", text):
            semesters.append(6)
        if re.search(r"\b(7th|seventh)\s+semester\b", text):
            semesters.append(7)
        if re.search(r"\b(8th|eighth|final\s+semester)\b", text):
            semesters.append(8)

        if "final year" in text or "last year" in text or "graduating" in text:
            semesters.extend([7, 8])
        if "fresh graduate" in text or "graduated" in text:
            semesters.extend([8]) # Post-graduation / terminal semester

        # General degree-wide or all semesters
        if "all undergraduate" in text or "enrolled in any semester" in text or "all semesters" in text:
            return [1, 2, 3, 4, 5, 6, 7, 8]

        return sorted(list(set(semesters)))
