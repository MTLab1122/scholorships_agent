"""Agent 9: Deadline Monitoring Agent.
Monitors approaching opportunity deadlines across configurable alert windows
(30d, 15d, 7d, 3d, 1d) with idempotent notification generation and timezone awareness.
"""

import datetime
import logging
from typing import List, Dict, Any, Optional
from agent.models import ScholarshipRecord
from agent.db import Database

logger = logging.getLogger(__name__)

DEFAULT_ALERT_WINDOWS = [30, 15, 7, 3, 1]
PKT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=5))


class DeadlineMonitoringAgent:
    def __init__(
        self,
        alert_windows: Optional[List[int]] = None,
        db: Optional[Database] = None
    ):
        self.alert_windows = sorted(alert_windows or DEFAULT_ALERT_WINDOWS, reverse=True)
        self.db = db

    def evaluate_deadlines(
        self,
        opportunities: List[ScholarshipRecord],
        today_date: Optional[datetime.date] = None
    ) -> List[Dict[str, Any]]:
        """Scans active opportunities and generates alert events for upcoming deadlines."""
        today = today_date or datetime.datetime.now(PKT_TIMEZONE).date()
        alerts: List[Dict[str, Any]] = []

        for opp in opportunities:
            if opp.status in ["Closed", "Previous cycle – awaiting new call"]:
                continue
            if not opp.deadline or opp.deadline == "not stated":
                continue

            try:
                deadline_dt = datetime.datetime.strptime(opp.deadline[:10], "%Y-%m-%d").date()
                days_left = (deadline_dt - today).days
            except Exception:
                continue

            if days_left < 0:
                continue

            for window in self.alert_windows:
                # Trigger alert if days_left matches window exactly or falls in immediate warning
                if days_left == window or (window == 7 and 0 <= days_left <= 7):
                    urgency = "URGENT" if days_left <= 3 else ("HIGH" if days_left <= 7 else "UPCOMING")
                    dedup_key = f"{opp.id}:deadline_{window}d:{today.strftime('%Y-%m-%d')}"
                    
                    alert = {
                        "opportunity_id": opp.id,
                        "opportunity_name": opp.name,
                        "sponsor": opp.sponsor,
                        "deadline": opp.deadline,
                        "days_left": days_left,
                        "window_triggered": window,
                        "urgency": urgency,
                        "title": f"[{urgency}] {opp.name} closes in {days_left} day{'s' if days_left != 1 else ''}!",
                        "message": (
                            f"The application deadline for '{opp.name}' by {opp.sponsor} is approaching on {opp.deadline} "
                            f"({days_left} days remaining). Please finalize required documents and submit via: {opp.apply_url}"
                        ),
                        "apply_url": opp.apply_url,
                        "dedup_key": dedup_key,
                        "generated_at": datetime.datetime.now(PKT_TIMEZONE).isoformat()
                    }
                    alerts.append(alert)
                    break # Take the most specific window

        logger.info(f"DeadlineMonitoringAgent: Generated {len(alerts)} alerts for active opportunities.")
        return alerts

    def dispatch_alerts_to_db(self, alerts: List[Dict[str, Any]], student_id: Optional[str] = None) -> int:
        """Saves idempotent notification records into the database."""
        if not self.db:
            return 0
        saved = 0
        with self.db.get_connection() as conn:
            for a in alerts:
                try:
                    cursor = conn.execute("""
                    INSERT OR IGNORE INTO notifications (
                        student_id, opportunity_id, channel, title, message,
                        notification_type, sent_at, dedup_key
                    ) VALUES (?, ?, 'in_app', ?, ?, 'deadline', ?, ?)
                    """, (
                        student_id or "ALL",
                        a["opportunity_id"],
                        a["title"],
                        a["message"],
                        a["generated_at"],
                        a["dedup_key"]
                    ))
                    if cursor.rowcount > 0:
                        saved += 1
                except Exception as e:
                    logger.debug(f"Notification insertion skipped: {e}")
            conn.commit()
        return saved

    def scan_deadlines(self, today_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """Convenience method for orchestrator to evaluate deadlines against database opportunities."""
        opportunities = self.db.list_opportunities() if self.db else []
        alerts = self.evaluate_deadlines(opportunities, today_date)
        saved = self.dispatch_alerts_to_db(alerts)
        return {
            "total_checked": len(opportunities),
            "alerts_triggered": len(alerts),
            "notifications_saved": saved,
            "alerts": alerts
        }

