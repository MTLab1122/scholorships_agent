"""Agent 8: Personalized Recommendation Agent.
Generates ranked, explainable shortlists for student profiles based on
confirmed eligibility, academic relevance, urgency, and domicile priority.
Never promises that a student will secure a scholarship or internship.
"""

from typing import List, Dict, Any, Optional
from agent.models import ScholarshipRecord, StudentProfile, StudentMatch
from agent.agents.eligibility_agent import EligibilityVerificationAgent


class PersonalizedRecommendationAgent:
    def __init__(self, eligibility_agent: Optional[EligibilityVerificationAgent] = None):
        self.eligibility_agent = eligibility_agent or EligibilityVerificationAgent()

    def generate_recommendations(
        self,
        student: StudentProfile,
        opportunities: List[ScholarshipRecord],
        limit: int = 25
    ) -> List[StudentMatch]:
        """Calculates multi-factor score and produces a ranked match list with explanations."""
        matches: List[StudentMatch] = []

        for opp in opportunities:
            eval_res = self.eligibility_agent.evaluate_eligibility(student, opp)
            if not eval_res["is_eligible"]:
                continue

            score = 50.0 # Base score for confirmed/likely eligible
            reasons = list(eval_res["reasons"])
            unmet = list(eval_res["unmet_criteria"])
            unknown = list(eval_res["unknown_criteria"])

            # 1. Domicile & Regional Weighting
            if opp.charsadda_flag:
                if student.domicile_district.lower() == "charsadda":
                    score += 25.0
                    reasons.append("Highest Priority: Opportunity targets Charsadda district domicile.")
                else:
                    score += 10.0
            elif opp.kp_flag:
                score += 15.0
                reasons.append("High Priority: Opportunity targets Khyber Pakhtunkhwa domicile.")

            # 2. Target University Weighting
            if opp.target_uni_flag:
                score += 10.0
                reasons.append(f"Direct University Alignment: Targets {student.university}.")

            # 3. Urgency Weighting
            if opp.status == "Closing soon":
                score += 15.0
                reasons.append("Time Sensitive: Application closes within 7 days.")
            elif opp.status == "Open":
                score += 5.0

            # 4. Verified Source Bonus
            if opp.source_trust_tier == 1:
                score += 5.0
                reasons.append("Verified: Sourced directly from official sponsor/university portal.")

            # 5. Financial Need / Funding Match
            if student.funding_need == "high" and (opp.is_fully_funded or opp.is_need_based):
                score += 10.0
                reasons.append("Financial Alignment: Matches high funding need profile.")

            score = min(max(score, 0.0), 100.0)

            priority = "high" if score >= 80.0 else ("medium" if score >= 60.0 else "low")

            matches.append(StudentMatch(
                student_id=student.id,
                opportunity_id=opp.id,
                opportunity_name=opp.name,
                sponsor=opp.sponsor,
                category=opp.category,
                deadline=opp.deadline,
                match_score=round(score, 1),
                eligibility_status=eval_res["eligibility_status"],
                reasons=reasons,
                unmet_criteria=unmet,
                unknown_criteria=unknown,
                recommended_priority=priority
            ))

        # Sort by match score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches[:limit]

    def rank_opportunities(
        self,
        student: Any,
        opportunities: List[ScholarshipRecord],
        top_n: int = 15
    ) -> List[StudentMatch]:
        """Convenience method accepting StudentProfile or student dict."""
        if isinstance(student, dict):
            student_obj = StudentProfile(
                id=student.get("id", ""),
                full_name=student.get("full_name") or student.get("name", "Student"),
                email=student.get("email", ""),
                university=student.get("university", "University of Peshawar"),
                university_type=student.get("university_type", "public"),
                degree_level=student.get("degree_level", "Undergraduate"),
                discipline=student.get("discipline", "Computer Science"),
                current_semester=int(student.get("current_semester", 1)),
                cgpa=float(student.get("cgpa", 3.0)),
                domicile_district=student.get("domicile_district", "Charsadda"),
                domicile_province=student.get("domicile_province", "Khyber Pakhtunkhwa"),
                work_preference=student.get("work_preference", "any"),
                funding_need=student.get("funding_need", "any"),
                skills=student.get("skills", []),
                interests=student.get("interests", [])
            )
        else:
            student_obj = student

        return self.generate_recommendations(student_obj, opportunities, limit=top_n)

