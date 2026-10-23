"""Agent 4: Eligibility Verification Agent.
Evaluates student eligibility against published criteria using deterministic rules.
Produces structured verdicts: confirmed_eligible, likely_eligible, not_eligible,
or insufficient_information with verbatim evidence and transparent reasoning.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from agent.models import ScholarshipRecord, StudentProfile

logger = logging.getLogger(__name__)


class EligibilityVerificationAgent:
    def evaluate_eligibility(
        self,
        student: StudentProfile,
        opp: ScholarshipRecord
    ) -> Dict[str, Any]:
        """Evaluates whether student meets the criteria for the given opportunity."""
        reasons: List[str] = []
        unmet: List[str] = []
        unknown: List[str] = []

        # 1. Nationality & Domicile Check
        dom_req = (opp.domicile_requirements or "").lower()
        if opp.is_international and not opp.kp_eligibility == "yes" and "pakistan" not in dom_req:
            unmet.append("Opportunity restricted to foreign or non-Pakistani nationals.")
        elif opp.charsadda_flag:
            if student.domicile_district.lower() == "charsadda":
                reasons.append("Exact match: Charsadda domicile priority satisfied.")
            else:
                reasons.append("Charsadda prioritized, but student has KP domicile.")
        elif opp.kp_flag:
            if student.domicile_province.lower() in ["khyber pakhtunkhwa", "kp"]:
                reasons.append("KP domicile criteria satisfied.")
            else:
                unmet.append("Requires Khyber Pakhtunkhwa (KP) domicile.")
        elif opp.pakistan_wide_kp_eligible:
            reasons.append("Open to all Pakistani nationals.")

        # 2. University Sector Check (Public vs Private)
        u_types = (opp.university_types or "").lower()
        s_uni_type = (student.university_type or "public").lower()
        if u_types in ["public", "private"] and u_types != "both" and u_types != "not stated":
            if u_types != s_uni_type:
                unmet.append(f"Opportunity is restricted to {u_types}-sector universities, but student attends {s_uni_type}-sector institution.")
            else:
                reasons.append(f"University sector matches requirement ({u_types}).")

        # 3. Target University Check
        el_inst = (opp.eligible_institutions or "").lower()
        if el_inst != "not stated" and len(el_inst) > 5:
            s_uni = student.university.lower()
            if any(term in el_inst for term in [s_uni, "all recognized", "hec recognized", "hec-recognised", "all universities"]):
                reasons.append(f"Student institution '{student.university}' is eligible.")
            elif opp.target_uni_flag and any(kw in s_uni for kw in ["peshawar", "bacha khan", "uet", "abasyn"]):
                reasons.append(f"Target university '{student.university}' matches program scope.")
            else:
                # If specific universities are listed and student is not in them
                if "uop" in el_inst and "peshawar" not in s_uni:
                    unmet.append(f"Restricted to {opp.eligible_institutions}.")

        # 4. Semester Eligibility Check
        if opp.eligible_semesters and len(opp.eligible_semesters) > 0:
            if student.current_semester in opp.eligible_semesters:
                reasons.append(f"Current semester ({student.current_semester}) is in eligible range {opp.eligible_semesters}.")
            else:
                unmet.append(f"Requires semester in {opp.eligible_semesters}, but student is currently in Semester {student.current_semester}.")
        else:
            # If not stated, do not infer that every semester is eligible
            unknown.append("Specific semester eligibility not published on source announcement.")

        # 5. CGPA Threshold Check
        min_gpa_text = (opp.min_gpa_or_marks or "").lower()
        if min_gpa_text != "not stated":
            gpa_match = re.search(r"\b([234]\.\d{1,2})\b", min_gpa_text)
            if gpa_match:
                req_gpa = float(gpa_match.group(1))
                if student.cgpa >= req_gpa:
                    reasons.append(f"Student CGPA ({student.cgpa:.2f}) meets minimum threshold ({req_gpa:.2f}).")
                else:
                    unmet.append(f"Student CGPA ({student.cgpa:.2f}) is below minimum requirement ({req_gpa:.2f}).")
            else:
                unknown.append(f"Complex merit criteria: {opp.min_gpa_or_marks}")

        # 6. Degree Level Check
        deg_req = (opp.degree_levels or "").lower()
        s_deg = student.degree_level.lower()
        if deg_req != "not stated":
            if "undergraduate" in deg_req or "bs" in deg_req or "bachelor" in deg_req:
                if "undergraduate" in s_deg or "bs" in s_deg:
                    reasons.append("Undergraduate degree level requirement matched.")
                else:
                    unmet.append(f"Requires undergraduate standing, student is {student.degree_level}.")
            elif "master" in deg_req or "ms" in deg_req or "phd" in deg_req:
                if "master" in s_deg or "ms" in s_deg or "phd" in s_deg:
                    reasons.append("Postgraduate degree level requirement matched.")
                else:
                    unmet.append(f"Requires postgraduate standing ({opp.degree_levels}), student is {student.degree_level}.")

        # 7. Final Status Determination
        if unmet:
            verdict = "not_eligible"
        elif unknown and not reasons:
            verdict = "insufficient_information"
        elif unknown and reasons:
            verdict = "likely_eligible"
        else:
            verdict = "confirmed_eligible"

        return {
            "eligibility_status": verdict,
            "reasons": reasons,
            "unmet_criteria": unmet,
            "unknown_criteria": unknown,
            "is_eligible": verdict in ["confirmed_eligible", "likely_eligible"]
        }
