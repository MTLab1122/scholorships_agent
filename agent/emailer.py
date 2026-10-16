"""Email delivery module using Resend API.
Handles:
- Email body with executive summary
- HTML, PDF, XLSX, and CSV report attachments
- Degraded mode subject prefix ([DEGRADED])
- Zero opportunities handling
- Local preview saving when API key is absent
"""

import os
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from agent.models import ReportSummary

logger = logging.getLogger(__name__)


class ResendEmailer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY", "")
        self.from_email = from_email or os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        self.to_email = to_email or os.environ.get("RESEND_TO_EMAIL", "")

    def send_daily_reports(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        attachment_paths: List[Path],
        degraded: bool = False,
        today_pkt: str = ""
    ) -> bool:
        """Composes and delivers the daily scholarship intelligence email via Resend."""
        total_opps = public_summary.total_opportunities + private_summary.total_opportunities
        total_charsadda = public_summary.charsadda_eligible_count + private_summary.charsadda_eligible_count
        closing_soon = public_summary.closing_within_7_days + private_summary.closing_within_7_days

        subject_prefix = "[DEGRADED] " if degraded else ""
        subject = (
            f"{subject_prefix}KP & Charsadda Scholarships Daily Report ({today_pkt}) — "
            f"{total_opps} Opportunities ({total_charsadda} Charsadda, {closing_soon} Closing Soon)"
        )

        email_html = self._build_email_html(
            public_summary=public_summary,
            private_summary=private_summary,
            today_pkt=today_pkt,
            degraded=degraded
        )

        # Build attachments
        attachments = []
        for p in attachment_paths:
            path = Path(p)
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        content_bytes = f.read()
                        b64_content = base64.b64encode(content_bytes).decode("utf-8")
                        attachments.append({
                            "filename": path.name,
                            "content": b64_content
                        })
                except Exception as e:
                    logger.warning(f"Failed to read attachment {path}: {e}")

        # If no API key or recipient, save local email preview and return success
        if not self.api_key or not self.to_email:
            logger.info("RESEND_API_KEY or RESEND_TO_EMAIL not provided. Writing email preview to reports directory.")
            if attachment_paths:
                preview_path = attachment_paths[0].parent / "email_preview.html"
                try:
                    with open(preview_path, "w", encoding="utf-8") as f:
                        f.write(email_html)
                    logger.info(f"Saved email preview to {preview_path}")
                except Exception as e:
                    logger.warning(f"Could not save email preview: {e}")
            return True

        # Send via Resend REST API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": self.from_email,
            "to": [self.to_email] if isinstance(self.to_email, str) else self.to_email,
            "subject": subject,
            "html": email_html,
            "attachments": attachments
        }

        try:
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=30)
            if resp.status_code in [200, 201]:
                logger.info(f"Email delivered successfully via Resend: ID {resp.json().get('id')}")
                return True
            else:
                logger.error(f"Resend API error HTTP {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Resend API: {e}")
            return False

    def _build_email_html(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        today_pkt: str,
        degraded: bool
    ) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>KP & Charsadda Scholarships Intelligence</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px;">
  <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 28px 24px;">
      <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #38bdf8; letter-spacing: 0.05em; margin-bottom: 6px;">
        Daily Intelligence Bulletin • 07:00 PKT
      </div>
      <h2 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 800; color: #f8fafc;">
        KP & Charsadda Scholarships Intelligence
      </h2>
      <div style="font-size: 13px; color: #cbd5e1;">
        Report Date: <strong>{today_pkt}</strong> | Run ID: <strong>{public_summary.run_id}</strong>
      </div>
    </div>

    <!-- Degraded Banner -->
    {"<div style='background: #fee2e2; border-left: 4px solid #b91c1c; color: #b91c1c; padding: 12px 18px; font-size: 13px; font-weight: 600;'>[DEGRADED RUN] Over 50% of seed sources could not be reached. Verified active listings and previously confirmed records are preserved.</div>" if degraded else ""}

    <div style="padding: 24px;">
      <p style="font-size: 14px; line-height: 1.5; color: #334155; margin-top: 0;">
        Assalam-o-Alaikum, here is your daily verified scholarship and financial aid report for students with a
        <strong>Khyber Pakhtunkhwa (KP) domicile</strong>, with top priority given to <strong>Charsadda district</strong>
        domicile holders and target universities.
      </p>

      <!-- Key Metrics Table -->
      <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
        <thead>
          <tr style="background-color: #f1f5f9; text-align: left;">
            <th style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">Sector Audience</th>
            <th style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">Total Active</th>
            <th style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;">Closing in ≤7d</th>
            <th style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #b45309;">Charsadda Priority</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0;"><strong>Report A: Public Universities</strong><br><span style="font-size: 11px; color: #64748b;">(UoP, UET Peshawar, BKUC, KMU, AUP, IMSciences)</span></td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; font-size: 15px; font-weight: 700;">{public_summary.total_opportunities}</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #b91c1c; font-weight: 700;">{public_summary.closing_within_7_days}</td>
            <td style="padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #b45309; font-weight: 700;">{public_summary.charsadda_eligible_count}</td>
          </tr>
          <tr>
            <td style="padding: 10px 14px;"><strong>Report B: Private Universities</strong><br><span style="font-size: 11px; color: #64748b;">(Abasyn University Peshawar, CECOS, INU, CUSIT)</span></td>
            <td style="padding: 10px 14px; font-size: 15px; font-weight: 700;">{private_summary.total_opportunities}</td>
            <td style="padding: 10px 14px; color: #b91c1c; font-weight: 700;">{private_summary.closing_within_7_days}</td>
            <td style="padding: 10px 14px; color: #b45309; font-weight: 700;">{private_summary.charsadda_eligible_count}</td>
          </tr>
        </tbody>
      </table>

      <!-- Attachments Notice -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #0f172a;">Attached Downloadable Reports:</h4>
        <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #475569; line-height: 1.6;">
          <li><code>public_scholarships_report_{today_pkt}.html / .pdf / .xlsx / .csv</code></li>
          <li><code>private_scholarships_report_{today_pkt}.html / .pdf / .xlsx / .csv</code></li>
        </ul>
      </div>

      <p style="font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 0;">
        All opportunities have been crawled and verified against official Pakistani domains (<code>*.gov.pk</code>, <code>*.edu.pk</code>) and vetted sponsor portals.
        Open the attached HTML report for full interactive details and print layouts.
      </p>
    </div>

    <!-- Footer -->
    <div style="background-color: #f1f5f9; padding: 14px 24px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0;">
      KP & Charsadda Daily Scholarship Intelligence Agent • Automated Daily Pipeline
    </div>
  </div>
</body>
</html>
"""
