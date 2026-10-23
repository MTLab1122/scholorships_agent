"""Agent 11: Application Preparation Agent
Assists students in assembling verified application packets for scholarships,
internships, and research placements without fabricating credentials.
Generates document checklists, tailored SOP outlines, CV drafting suggestions,
recommendation letter templates, and interview prep questions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from agent.models import OpportunityRecord, StudentProfile


class ApplicationPreparationAgent:
    """Specialized Agent for student opportunity application readiness."""

    def __init__(self):
        pass

    def generate_preparation_packet(
        self,
        student: StudentProfile,
        opp: OpportunityRecord
    ) -> Dict[str, Any]:
        """Generates comprehensive, tailored application packet based strictly on official criteria."""
        checklist = self._build_document_checklist(opp, student)
        sop_framework = self._build_sop_framework(opp, student)
        cv_suggestions = self._build_cv_suggestions(opp, student)
        recommendation_template = self._build_recommendation_template(opp, student)
        interview_questions = self._build_interview_prep(opp, student)

        return {
            "opportunity_id": opp.id,
            "opportunity_name": opp.name,
            "sponsor": opp.sponsor,
            "deadline": opp.deadline or "Not Stated",
            "student_name": student.name,
            "target_degree": student.current_degree,
            "document_checklist": checklist,
            "statement_of_purpose_guide": sop_framework,
            "cv_focus_areas": cv_suggestions,
            "recommendation_letter_template": recommendation_template,
            "interview_prep_questions": interview_questions,
            "safety_disclosure": (
                "Notice: This agent synthesizes verified requirements from official announcements. "
                "All academic achievements, CGPA, and financial disclosures must be truthfully attested. "
                "No automated submission will occur without explicit student authorization."
            ),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _build_document_checklist(self, opp: OpportunityRecord, student: StudentProfile) -> List[Dict[str, Any]]:
        """Extracts required documents based on opportunity category and domicile requirements."""
        docs = [
            {
                "item": "Official Academic Transcripts & DMC",
                "detail": f"Latest transcript showing CGPA (Current CGPA: {student.cgpa}) attested by Controller of Examinations.",
                "required": True,
                "status": "pending"
            },
            {
                "item": "Valid CNIC / Smart Card / Form-B",
                "detail": "Front and back photocopies of NADRA CNIC or Form-B.",
                "required": True,
                "status": "pending"
            }
        ]

        # Domicile verification
        if opp.kp_eligibility == "yes" or opp.charsadda_eligibility == "yes" or opp.domicile_requirements != "not stated":
            docs.append({
                "item": "Official Domicile Certificate",
                "detail": f"Attested domicile certificate for {student.domicile_district}, {student.domicile_province}.",
                "required": True,
                "status": "pending"
            })

        # Income slips for need-based
        if opp.is_need_based or (opp.income_cap and opp.income_cap != "not stated") or opp.need_criteria != "not stated":
            docs.append({
                "item": "Parent / Guardian Salary Slip or Income Certificate",
                "detail": "Latest verified salary slip, pension book, or Tehsildar income affidavit for family income verification.",
                "required": True,
                "status": "pending"
            })
            docs.append({
                "item": "Utility Bills (Last 3 Months)",
                "detail": "Electricity, gas, and water bill paid receipts as evidence of household expenditure.",
                "required": True,
                "status": "pending"
            })

        # University Enrolment Bonafide Certificate
        docs.append({
            "item": "University Bonafide Certificate & Fee Slip",
            "detail": f"Attestation from Head of Department confirming enrolment in {student.current_degree} (Semester {student.current_semester}) at {student.university_name}.",
            "required": True,
            "status": "pending"
        })

        # Parse any specific required_documents from record
        if opp.required_documents and opp.required_documents != "not stated":
            docs.append({
                "item": "Opportunity-Specific Attachments",
                "detail": opp.required_documents,
                "required": True,
                "status": "pending"
            })

        return docs

    def _build_sop_framework(self, opp: OpportunityRecord, student: StudentProfile) -> Dict[str, Any]:
        """Provides structured, honest statement-of-purpose prompts based on student profile."""
        return {
            "title": f"Statement of Purpose Outline for {opp.name}",
            "suggested_length": "500 - 800 words",
            "section_prompts": [
                {
                    "section": "1. Introduction & Academic Background",
                    "guidance": (
                        f"State your current program ({student.current_degree} at {student.university_name}) and major in {student.discipline}. "
                        "Highlight your genuine passion for this field and why you are pursuing this specific opportunity."
                    )
                },
                {
                    "section": "2. Academic Track Record & Key Projects",
                    "guidance": (
                        f"Discuss your academic performance (CGPA {student.cgpa}) and specific coursework or semester projects. "
                        f"Mention skills you have developed, including {', '.join(student.skills) if student.skills else 'relevant technical tools'}."
                    )
                },
                {
                    "section": "3. Motivation for this Award / Position",
                    "guidance": (
                        f"Explain why {opp.sponsor}'s mission resonates with your goals. "
                        f"Cite specific aspects of the opportunity ({opp.award_amount or opp.benefits or 'academic support'})."
                    )
                },
                {
                    "section": "4. Community Impact & Career Vision",
                    "guidance": (
                        f"Explain how this opportunity will empower you to serve your community in {student.domicile_district} "
                        "and contribute to technological/economic development in Pakistan upon graduation."
                    )
                }
            ]
        }

    def _build_cv_suggestions(self, opp: OpportunityRecord, student: StudentProfile) -> List[str]:
        """Highlights key focus areas for candidate's curriculum vitae."""
        suggestions = [
            f"Set primary header with contact info, LinkedIn, GitHub (if tech), and residential city ({student.domicile_district}).",
            f"Education: List '{student.current_degree}' at '{student.university_name}', specifying current semester {student.current_semester} and CGPA {student.cgpa}.",
        ]
        if student.skills:
            suggestions.append(f"Technical Skills: Group into Languages, Frameworks, and Tools: {', '.join(student.skills)}.")
        if opp.category == "internships":
            suggestions.append("Experience/Projects: Emphasize practical lab projects, open-source code repositories, or previous internships.")
        if opp.category == "scholarships":
            suggestions.append("Honors & Leadership: Include merit certificates, dean's list citations, and student society participation.")
        return suggestions

    def _build_recommendation_template(self, opp: OpportunityRecord, student: StudentProfile) -> str:
        """Formal faculty recommendation request email template."""
        return f"""Subject: Letter of Recommendation Request — {student.name} ({student.current_degree}, Sem {student.current_semester})

Respected Professor [Professor Name],

I hope this email finds you well.

I am writing to respectfully ask if you would consider writing a letter of recommendation for my application to the "{opp.name}", offered by {opp.sponsor}.

I am currently in Semester {student.current_semester} of the {student.current_degree} program at {student.university_name}, maintaining a CGPA of {student.cgpa}. I thoroughly enjoyed your course, [Course Name], where I particularly appreciated [mention a specific lab, presentation, or project completed in their class].

The application deadline for this opportunity is {opp.deadline or '[Target Date]'}. The opportunity requires an evaluation of my academic commitment, character, and potential in {student.discipline}.

To make this as convenient as possible for you, I have attached my latest transcript, CV, and a brief draft of my statement of purpose. If you are willing to support my candidacy, please let me know and I will provide the submission link or letterhead guidelines.

Thank you very much for your continuous guidance and support.

Warm regards,

{student.name}
Roll Number / Registration ID: [Your ID]
Department of {student.discipline}
{student.university_name}
Email: {student.email}
Phone: [Your Contact Number]
"""

    def _build_interview_prep(self, opp: OpportunityRecord, student: StudentProfile) -> List[Dict[str, str]]:
        """Anticipated interview questions tailored to the opportunity type."""
        questions = [
            {
                "question": "Tell us about yourself and your academic journey so far.",
                "tip": "Keep it under 90 seconds. Focus on your university background, key projects, and future direction."
            },
            {
                "question": f"Why did you choose to apply for {opp.name} with {opp.sponsor}?",
                "tip": "Demonstrate knowledge of their organization and how their objectives align with your studies."
            },
            {
                "question": f"How do you balance demanding coursework in {student.discipline} with extracurriculars or research?",
                "tip": "Provide a concrete time-management example (e.g. agile task planning or study calendars)."
            }
        ]
        if opp.is_need_based:
            questions.append({
                "question": "How will this scholarship impact your family and academic continuity?",
                "tip": "Be honest and dignified regarding family finances, explaining how the stipend relieves tuition pressure."
            })
        if opp.category in ["internships", "fyp_industry_projects", "research_fellowships"]:
            questions.append({
                "question": "Describe a difficult technical bug or project obstacle you encountered and how you resolved it.",
                "tip": "Use the STAR framework (Situation, Task, Action, Result) focusing on your analytical thought process."
            })
        return questions
