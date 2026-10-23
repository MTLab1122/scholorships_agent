import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from agent.emailer import ResendEmailer, _sanitize_recipient
from agent.models import ReportSummary


def test_sanitize_recipient():
    assert _sanitize_recipient("  user@example.com  ") == "user@example.com"
    assert _sanitize_recipient("") == ""


def test_emailer_primary_recipient_enforced():
    with patch.dict(os.environ, {"OWNER_EMAIL": "primary.owner@example.com", "RECIPIENT_EMAIL": ""}):
        emailer = ResendEmailer()
        assert emailer.owner_email == "primary.owner@example.com"
        assert not hasattr(emailer, "forward_email")

    with patch.dict(os.environ, {"RECIPIENT_EMAIL": "recipient.owner@example.com", "OWNER_EMAIL": ""}):
        emailer = ResendEmailer()
        assert emailer.owner_email == "recipient.owner@example.com"


def test_emailer_recipient_list_sanitization():
    emailer = ResendEmailer(to_email=["user1@example.com", "user2@example.com"])
    assert "user1@example.com" in emailer.to_email
    assert "user2@example.com" in emailer.to_email


def test_emailer_raises_loud_exception_on_failure(tmp_path):
    """Verify that SMTP/API delivery failures raise loud exceptions rather than failing silently."""
    emailer = ResendEmailer(api_key="", to_email="owner@example.com")
    # Empty credentials and no mock will trigger failure
    summary = ReportSummary(
        title="Test Report",
        audience="Public",
        generated_at_pkt="2026-10-23 07:00 PKT",
        run_id="RUN-TEST",
        sources_checked_count=5,
        total_opportunities=10,
        new_since_yesterday=2,
        closing_within_7_days=1,
        charsadda_eligible_count=3,
        kp_eligible_count=8,
        broken_links_count=0,
        degraded_mode=False
    )
    with patch.dict(os.environ, {"GMAIL_USER": "", "GMAIL_APP_PASSWORD": ""}):
        with pytest.raises(RuntimeError) as exc_info:
            emailer.send_daily_reports(
                public_summary=summary,
                private_summary=summary,
                attachment_paths=[],
                degraded=False,
                today_pkt="2026-10-23",
                dry_run=False
            )
        assert "FATAL: Email delivery to primary recipient" in str(exc_info.value)


def test_emailer_dry_run_saves_preview(tmp_path):
    emailer = ResendEmailer(api_key="", to_email="owner@example.com")
    summary = ReportSummary(
        title="Test Report",
        audience="Public",
        generated_at_pkt="2026-10-23 07:00 PKT",
        run_id="RUN-TEST",
        sources_checked_count=5,
        total_opportunities=10,
        new_since_yesterday=2,
        closing_within_7_days=1,
        charsadda_eligible_count=3,
        kp_eligible_count=8,
        broken_links_count=0,
        degraded_mode=False
    )
    report_file = tmp_path / "test_report.pdf"
    report_file.write_bytes(b"%PDF-1.4 mock")

    success = emailer.send_daily_reports(
        public_summary=summary,
        private_summary=summary,
        attachment_paths=[report_file],
        degraded=False,
        today_pkt="2026-10-23",
        dry_run=True,
        deadline_alerts=[{"urgency": "URGENT", "opportunity_name": "Test Alert", "deadline": "2026-10-25", "days_left": 2}],
        agent_telemetry={"Discovery Agent": "10 found"}
    )
    assert success is True
    preview_file = tmp_path / "email_preview.html"
    assert preview_file.exists()
    content = preview_file.read_text(encoding="utf-8")
    assert "KP &amp; Charsadda Scholarships Intelligence" in content or "KP & Charsadda Scholarships Intelligence" in content
    assert "Test Alert" in content

