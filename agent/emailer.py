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
import smtplib
from email.message import EmailMessage
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
        to_email: Optional[Any] = None,
    ):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY", "")
        self.from_email = from_email or os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        
        raw_to = to_email or os.environ.get("RECIPIENT_EMAIL") or os.environ.get("RESEND_TO_EMAIL", "")
        if isinstance(raw_to, str):
            self.to_email = [e.strip() for e in raw_to.split(",") if e.strip()]
        elif isinstance(raw_to, list):
            self.to_email = [e.strip() for e in raw_to if e.strip()]
        else:
            self.to_email = []

    def send_daily_reports(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        attachment_paths: List[Path],
        degraded: bool = False,
        today_pkt: str = "",
        dry_run: bool = False
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
            degraded=degraded,
            attachment_paths=attachment_paths
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

        # If dry-run or no recipient, save local email preview and return success
        if dry_run or not self.to_email:
            logger.info("Dry-run active or no recipient configured. Writing email preview to reports directory.")
            if attachment_paths:
                preview_path = attachment_paths[0].parent / "email_preview.html"
                try:
                    with open(preview_path, "w", encoding="utf-8") as f:
                        f.write(email_html)
                    logger.info(f"Saved email preview to {preview_path}")
                except Exception as e:
                    logger.warning(f"Could not save email preview: {e}")
            return True

        # Check if Gmail / SMTP configuration is provided (direct sending from Gmail)
        smtp_user = os.environ.get("GMAIL_USER") or os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("SMTP_PASSWORD")
        if smtp_user and smtp_pass:
            logger.info(f"Using direct Gmail SMTP to send report from {smtp_user} to {self.to_email}")
            return self._send_via_smtp(self.to_email, subject, email_html, attachment_paths)

        # Fallback to Resend REST API if Resend API key is present
        if not self.api_key:
            logger.warning("Neither Gmail credentials (GMAIL_USER, GMAIL_APP_PASSWORD) nor RESEND_API_KEY provided.")
            if attachment_paths:
                preview_path = attachment_paths[0].parent / "email_preview.html"
                try:
                    with open(preview_path, "w", encoding="utf-8") as f:
                        f.write(email_html)
                    logger.info(f"Saved email preview to {preview_path}")
                except Exception as e:
                    logger.warning(f"Could not save email preview: {e}")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        recipients = self.to_email if isinstance(self.to_email, list) else [self.to_email]
        payload = {
            "from": self.from_email,
            "to": recipients,
            "subject": subject,
            "html": email_html,
            "attachments": attachments
        }

        try:
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=30)
            if resp.status_code in [200, 201]:
                logger.info(f"Email delivered successfully via Resend to {recipients}: ID {resp.json().get('id')}")
                return True
            elif resp.status_code == 403 and len(recipients) > 1:
                logger.warning(
                    f"Resend multi-recipient send rejected ({resp.text}). "
                    "Attempting individual deliveries for each recipient..."
                )
                any_success = False
                for rec in recipients:
                    sub_payload = dict(payload)
                    sub_payload["to"] = [rec]
                    try:
                        sub_resp = requests.post("https://api.resend.com/emails", json=sub_payload, headers=headers, timeout=30)
                        if sub_resp.status_code in [200, 201]:
                            logger.info(f"Delivered to {rec} via Resend: ID {sub_resp.json().get('id')}")
                            any_success = True
                        else:
                            logger.error(
                                f"Failed to deliver to {rec} via Resend (HTTP {sub_resp.status_code}): {sub_resp.text}. "
                                "Note: When using onboarding@resend.dev, Resend only allows sending to the account owner email."
                            )
                    except Exception as sub_e:
                        logger.error(f"Error delivering to {rec}: {sub_e}")
                return any_success
            else:
                logger.error(f"Resend API error HTTP {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Resend API: {e}")
            return False

    def _send_via_smtp(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        attachment_paths: List[Path]
    ) -> bool:
        """Delivers daily scholarship reports via standard SMTP (e.g. Gmail)."""
        smtp_user = os.environ.get("SMTP_USER") or os.environ.get("GMAIL_USER")
        smtp_pass = os.environ.get("SMTP_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD")
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "465"))

        if not smtp_user or not smtp_pass:
            return False

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"Muhammad Talha <{smtp_user}>"
            msg["To"] = ", ".join(to_addresses)
            msg.set_content("Please enable HTML to view this report.")
            msg.add_alternative(html_body, subtype="html")

            for path in attachment_paths:
                p = Path(path)
                if p.exists():
                    with open(p, "rb") as f:
                        file_data = f.read()
                    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=p.name)

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=45) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=45) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

            logger.info(f"Delivered email successfully via SMTP to {to_addresses}")
            return True
        except Exception as e:
            logger.error(f"SMTP delivery failed: {e}")
            return False

    def _build_email_html(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        today_pkt: str,
        degraded: bool,
        attachment_paths: Optional[List[Path]] = None
    ) -> str:
        if attachment_paths:
            att_items = "".join(f"<li><code>{Path(p).name}</code></li>" for p in attachment_paths)
        else:
            att_items = f"<li><code>public_scholarships_report_{today_pkt}.pdf</code></li><li><code>private_scholarships_report_{today_pkt}.pdf</code></li>"

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
        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #0f172a;">Attached PDF Reports:</h4>
        <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #475569; line-height: 1.6;">
          {att_items}
        </ul>
      </div>

      <p style="font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 0;">
        All opportunities have been crawled and verified against official Pakistani domains (<code>*.gov.pk</code>, <code>*.edu.pk</code>) and vetted sponsor portals.
        The attached PDF documents contain complete eligibility criteria, priority flags, and direct application links.
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
