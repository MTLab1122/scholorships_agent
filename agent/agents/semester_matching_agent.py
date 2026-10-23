import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from agent.models import ScholarshipRecord, StudentProfile, OpportunityRecord

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Structured evaluation verdict comparing student against opportunity criteria."""
    is_eligible: bool
    status: str = "confirmed_eligible" # "confirmed_eligible", "likely_eligible", "not_eligible", "insufficient_information"
    reasons: List[str] = Field(default_factory=list)
    unmet_criteria: List[str] = Field(default_factory=list)
    unknown_criteria: List[str] = Field(default_factory=list)


def _matches_discipline(student_discipline: str, opp_fields: str) -> bool:
    s_disc = (student_discipline or "").lower().strip()
    o_fields = (opp_fields or "").lower().strip()
    if not o_fields or o_fields in ["not stated", "all", "all disciplines", "any", "open to all"]:
        return True

    synonyms = {
        "computer science": ["cs", "computer", "software", "it", "information technology", "computing", "data science", "cyber"],
        "software engineering": ["se", "software", "computer", "cs", "it"],
        "pharmacy": ["pharmacy", "pharm-d", "pharmd", "pharmaceutical"],
        "medicine": ["medicine", "mbbs", "bds", "medical", "doctor"],
        "electrical engineering": ["electrical", "electronics", "telecom"],
        "civil engineering": ["civil"],
        "mechanical engineering": ["mechanical"],
        "business administration": ["bba", "mba", "business", "management", "commerce"],
        "economics": ["economics", "finance"],
    }

    if s_disc in o_fields:
        return True

    s_words = [w for w in re.split(r"[\s/,]+", s_disc) if len(w) > 2]
    for w in s_words:
        if w in o_fields:
            return True

    for key, alias_list in synonyms.items():
        if key in s_disc or any(a in s_disc for a in alias_list):
            if any(a in o_fields for a in alias_list) or key in o_fields:
                return True

    return False


class SemesterMatchingAgent:
    def evaluate_opportunity(
        self,
        student: StudentProfile,
        opp: OpportunityRecord
    ) -> EvaluationResult:
        """Evaluates whether student meets the criteria for the given opportunity.
        Checks university sector (public/private), semester range, degree level,
        discipline/field of study, CGPA, and domicile restrictions.
        """
        reasons: List[str] = []
        unmet: List[str] = []
        unknown: List[str] = []
        is_eligible = True

        # 1. University Sector Check (Public vs Private)
        u_types = (opp.university_types or "").lower().strip()
        s_uni_type = (student.university_type or "public").lower().strip()
        if u_types in ["public", "private"] and u_types != "both" and u_types != "not stated":
            if u_types != s_uni_type:
                reasons.append(f"Ineligible university sector: opportunity requires {u_types}-sector universities, student attends {s_uni_type}-sector institution.")
                unmet.append(f"Ineligible university sector: requires {u_types}")
                is_eligible = False
            else:
                reasons.append(f"University sector matches requirement ({u_types}).")

        # 2. Semester Range Check
        if opp.eligible_semesters and len(opp.eligible_semesters) > 0:
            if student.current_semester in opp.eligible_semesters:
                reasons.append(f"Current semester ({student.current_semester}) meets required range {opp.eligible_semesters}.")
            else:
                msg = f"Semester {student.current_semester} does not meet required range {opp.eligible_semesters}."
                reasons.append(msg)
                unmet.append(msg)
                is_eligible = False
        else:
            # Rule: If an opportunity does not specify semester eligibility, do not infer that every semester is accepted.
            unknown.append("Specific semester eligibility not published on source announcement.")

        # 3. Field of Study / Discipline Check
        if opp.fields_of_study and opp.fields_of_study.lower() != "not stated":
            if not _matches_discipline(student.discipline, opp.fields_of_study):
                msg = f"Student discipline '{student.discipline}' does not match required fields of study: {opp.fields_of_study}."
                reasons.append(msg)
                unmet.append(msg)
                is_eligible = False
            else:
                reasons.append(f"Discipline '{student.discipline}' is eligible under: {opp.fields_of_study}.")

        # 4. Degree Level Check
        deg_req = (opp.degree_levels or "").lower().strip()
        s_deg = (student.degree_level or "").lower().strip()
        if deg_req and deg_req != "not stated":
            if "undergraduate" in deg_req or "bs" in deg_req or "bachelor" in deg_req:
                if "undergraduate" in s_deg or "bs" in s_deg:
                    reasons.append("Undergraduate standing criteria satisfied.")
                else:
                    msg = f"Requires undergraduate standing, student degree level is {student.degree_level}."
                    reasons.append(msg)
                    unmet.append(msg)
                    is_eligible = False
            elif "master" in deg_req or "ms" in deg_req or "phd" in deg_req:
                if "master" in s_deg or "ms" in s_deg or "phd" in s_deg:
                    reasons.append("Postgraduate standing criteria satisfied.")
                else:
                    msg = f"Requires postgraduate standing ({opp.degree_levels}), student degree level is {student.degree_level}."
                    reasons.append(msg)
                    unmet.append(msg)
                    is_eligible = False

        # 5. Minimum CGPA Check
        if opp.min_gpa_or_marks and opp.min_gpa_or_marks.lower() != "not stated":
            gpa_match = re.search(r"\b([234]\.\d{1,2})\b", opp.min_gpa_or_marks)
            if gpa_match:
                req_gpa = float(gpa_match.group(1))
                if student.cgpa < req_gpa:
                    msg = f"Student CGPA ({student.cgpa:.2f}) is below minimum requirement ({req_gpa:.2f})."
                    reasons.append(msg)
                    unmet.append(msg)
                    is_eligible = False
                else:
                    reasons.append(f"Student CGPA ({student.cgpa:.2f}) meets minimum requirement ({req_gpa:.2f}).")
            else:
                unknown.append(f"Complex merit criteria: {opp.min_gpa_or_marks}")

        # 6. Domicile & District Check
        if opp.charsadda_flag or opp.charsadda_eligibility == "yes":
            if student.domicile_district.lower() == "charsadda":
                reasons.append("Charsadda district domicile eligibility satisfied.")
            else:
                reasons.append("Charsadda prioritized, but student has other domicile.")
        elif opp.kp_flag or opp.kp_eligibility == "yes":
            if student.domicile_province.lower() in ["khyber pakhtunkhwa", "kp"]:
                reasons.append("Khyber Pakhtunkhwa (KP) domicile criteria satisfied.")
            else:
                msg = "Requires Khyber Pakhtunkhwa (KP) domicile."
                reasons.append(msg)
                unmet.append(msg)
                is_eligible = False

        # Status determination
        if unmet:
            status = "not_eligible"
        elif unknown and not reasons:
            status = "insufficient_information"
        elif unknown and reasons:
            status = "likely_eligible"
        else:
            status = "confirmed_eligible"

        return EvaluationResult(
            is_eligible=is_eligible and len(unmet) == 0,
            status=status,
            reasons=reasons,
            unmet_criteria=unmet,
            unknown_criteria=unknown
        )

    def filter_by_semester(
        self,
        records: List[ScholarshipRecord],
        target_semester: int,
        degree_level: str = "Undergraduate",
        university_type: Optional[str] = None
    ) -> List[ScholarshipRecord]:
        """Filters opportunities suitable for a student in a specific semester and sector."""
        matched: List[ScholarshipRecord] = []
        u_type_clean = (university_type or "").lower().strip()

        for r in records:
            # 1. Sector Check
            if u_type_clean and u_type_clean in ["public", "private"]:
                r_uni_types = (r.university_types or "").lower()
                if r_uni_types in ["public", "private"] and r_uni_types != u_type_clean:
                    continue

            # 2. Degree Level Check
            deg_req = (r.degree_levels or "").lower()
            if deg_req != "not stated":
                if "undergraduate" in degree_level.lower() or "bs" in degree_level.lower():
                    if not any(kw in deg_req for kw in ["undergraduate", "bs", "bachelor", "all"]):
                        continue
                elif "master" in degree_level.lower() or "ms" in degree_level.lower():
                    if not any(kw in deg_req for kw in ["master", "ms", "postgraduate", "all"]):
                        continue

            # 3. Semester Check
            if r.eligible_semesters and len(r.eligible_semesters) > 0:
                if target_semester in r.eligible_semesters:
                    matched.append(r)
            else:
                # If no specific semester is restricted, check if general academic_years mentions it
                ay_text = (r.academic_years or "").lower()
                if "1st year" in ay_text and target_semester > 2:
                    continue
                if "final year" in ay_text and target_semester < 7:
                    continue
                matched.append(r)

        return matched

    def partition_by_academic_stage(
        self,
        records: List[ScholarshipRecord]
    ) -> Dict[str, List[ScholarshipRecord]]:
        """Groups opportunities into early-semester, mid-semester, and final-year categories."""
        stages = {
            "early_semesters_1_4": [],
            "mid_semesters_5_6": [],
            "final_year_7_8": [],
            "postgraduate_and_graduates": []
        }

        for r in records:
            deg = (r.degree_levels or "").lower()
            if "master" in deg or "phd" in deg:
                stages["postgraduate_and_graduates"].append(r)

            sems = r.eligible_semesters or []
            if not sems:
                # Open or degree-wide
                stages["early_semesters_1_4"].append(r)
                stages["mid_semesters_5_6"].append(r)
                stages["final_year_7_8"].append(r)
            else:
                if any(s in [1, 2, 3, 4] for s in sems):
                    stages["early_semesters_1_4"].append(r)
                if any(s in [5, 6] for s in sems):
                    stages["mid_semesters_5_6"].append(r)
                if any(s in [7, 8] for s in sems):
                    stages["final_year_7_8"].append(r)

        return stages
