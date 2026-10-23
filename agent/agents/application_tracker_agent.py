"""Agent 12: Application Tracking Agent
Manages private student opportunity applications, Kanban board workflow stages,
actionable checklist tasks, submission dates, and interview reminders.
Enforces strict student isolation and database synchronization.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from agent.models import ApplicationRecord, OpportunityRecord
from agent.db import OpportunityDB


VALID_STATUSES = [
    "interested",
    "checking_eligibility",
    "preparing_documents",
    "ready_to_apply",
    "applied",
    "interview_assessment",
    "awarded_accepted",
    "rejected",
    "withdrawn"
]


class ApplicationTrackingAgent:
    """Specialized Agent for student opportunity lifecycle and Kanban tracking."""

    def __init__(self, db: Optional[OpportunityDB] = None):
        self.db = db or OpportunityDB()

    def create_application(
        self,
        student_id: str,
        opportunity_id: str,
        initial_status: str = "interested",
        notes: str = ""
    ) -> ApplicationRecord:
        """Initializes a new tracked application for a student."""
        if initial_status not in VALID_STATUSES:
            raise ValueError(f"Invalid application status: {initial_status}. Allowed: {VALID_STATUSES}")

        opp = self.db.get_opportunity(opportunity_id)
        if opp:
            opp_name = opp.get("name") if isinstance(opp, dict) else getattr(opp, "name", "Custom Opportunity")
            sponsor = opp.get("sponsor") if isinstance(opp, dict) else getattr(opp, "sponsor", "Direct Application")
            deadline = opp.get("deadline") if isinstance(opp, dict) else getattr(opp, "deadline", "")
        else:
            opp_name = "Custom Opportunity"
            sponsor = "Direct Application"
            deadline = ""

        app_id = f"APP_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        # Build initial tasks
        default_tasks = [
            {"id": "t1", "title": "Review official eligibility guidelines", "completed": False},
            {"id": "t2", "title": "Gather required academic transcripts", "completed": False},
            {"id": "t3", "title": "Submit application before deadline", "completed": False}
        ]

        app_record = ApplicationRecord(
            id=app_id,
            student_id=student_id,
            opportunity_id=opportunity_id,
            opportunity_name=opp_name,
            sponsor=sponsor,
            status=initial_status,
            deadline=deadline or "",
            notes=notes,
            tasks=default_tasks,
            documents_checklist=[],
            created_at=now,
            updated_at=now
        )

        saved_id = self.db.save_application(app_record)
        app_record.id = saved_id
        return app_record

    def update_status(
        self,
        application_id: str,
        student_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> Optional[ApplicationRecord]:
        """Transitions an application to a new Kanban stage, verifying student ownership."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Allowed: {VALID_STATUSES}")

        app = self.db.get_application(application_id)
        if not app or app.student_id != student_id:
            return None # Student ownership guard

        app.status = new_status
        app.updated_at = datetime.now(timezone.utc).isoformat()
        if notes is not None:
            app.notes = notes

        self.db.save_application(app)
        return app

    def add_task(
        self,
        application_id: str,
        student_id: str,
        task_title: str
    ) -> Optional[ApplicationRecord]:
        """Adds a personalized task to the application checklist."""
        app = self.db.get_application(application_id)
        if not app or app.student_id != student_id:
            return None

        task_id = f"t_{uuid.uuid4().hex[:6]}"
        app.tasks.append({"id": task_id, "title": task_title, "completed": False})
        app.updated_at = datetime.now(timezone.utc).isoformat()
        self.db.save_application(app)
        return app

    def toggle_task(
        self,
        application_id: str,
        student_id: str,
        task_id: str
    ) -> Optional[ApplicationRecord]:
        """Toggles the completion status of an application task."""
        app = self.db.get_application(application_id)
        if not app or app.student_id != student_id:
            return None

        for t in app.tasks:
            if t.get("id") == task_id:
                t["completed"] = not t.get("completed", False)
                break

        app.updated_at = datetime.now(timezone.utc).isoformat()
        self.db.save_application(app)
        return app

    def get_student_applications(self, student_id: str) -> List[ApplicationRecord]:
        """Returns all private application records for a specific student."""
        return self.db.list_applications_for_student(student_id)

    def get_kanban_summary(self, student_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Groups a student's applications into Kanban columns."""
        apps = self.get_student_applications(student_id)
        columns: Dict[str, List[Dict[str, Any]]] = {status: [] for status in VALID_STATUSES}
        for a in apps:
            columns.setdefault(a.status, []).append(a.model_dump())
        return columns
