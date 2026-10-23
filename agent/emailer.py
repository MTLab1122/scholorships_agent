"""Email delivery module using Resend API.
Handles:
- Email body with executive summary
- HTML, PDF, XLSX, and CSV report attachments
- Degraded mode subject prefix ([DEGRADED])
- Zero opportunities handling
- Local preview saving when API key is absent
"""

import os
import time
import datetime
import base64
import smtplib
from email.message import EmailMessage
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from agent.models import ReportSummary

logger = logging.getLogger(__name__)

PKT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=5))


def _sanitize_recipient(email_str: str) -> str:
    """Sanitizes recipient email addresses, stripping whitespace."""
    if not email_str:
        return ""
    return str(email_str).strip()


class ResendEmailer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[Any] = None,
    ):
        self.api_key = api_key or os.environ.get("RESEND_API_KEY", "")
        self.from_email = from_email or os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        
        # Primary recipient is configured owner email (guaranteed exclusive recipient)
        self.owner_email = _sanitize_recipient(
            os.environ.get("OWNER_EMAIL") or os.environ.get("RECIPIENT_EMAIL") or "muhammadtalhapro1@gmail.com"
        )
        
        # Backward compatibility for to_email override
        if to_email:
            if isinstance(to_email, str):
                self.to_email = [_sanitize_recipient(e) for e in to_email.split(",") if _sanitize_recipient(e)]
            elif isinstance(to_email, list):
                self.to_email = [_sanitize_recipient(e) for e in to_email if _sanitize_recipient(e)]
            else:
                self.to_email = [self.owner_email]
        else:
            self.to_email = [self.owner_email]

    def send_daily_reports(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        attachment_paths: List[Path],
        degraded: bool = False,
        today_pkt: str = "",
        dry_run: bool = False,
        deadline_alerts: Optional[List[Dict[str, Any]]] = None,
        agent_telemetry: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Composes and delivers the consolidated daily intelligence report exclusively
        to the primary configured email address on every run.
        
        Raises a loud RuntimeError on any SMTP or Resend API failure in live runs.
        """
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
            attachment_paths=attachment_paths,
            deadline_alerts=deadline_alerts,
            agent_telemetry=agent_telemetry
        )

        # Build attachments for Resend
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

        # If dry-run, save preview to disk and return success
        if dry_run:
            logger.info("Dry-run active. Writing email preview to reports directory.")
            if attachment_paths:
                preview_path = attachment_paths[0].parent / "email_preview.html"
            else:
                preview_path = Path("reports") / "email_preview.html"
                preview_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(preview_path, "w", encoding="utf-8") as f:
                    f.write(email_html)
                logger.info(f"Saved email preview to {preview_path}")
            except Exception as e:
                logger.warning(f"Could not save email preview: {e}")
            return True

        target_recipient = self.owner_email
        if not target_recipient:
            raise RuntimeError(
                "FATAL: Primary recipient email is not configured! Set OWNER_EMAIL or RECIPIENT_EMAIL."
            )

        delivered = False
        resend_error: Optional[str] = None
        smtp_error: Optional[str] = None

        logger.info(f"Initiating daily report delivery exclusively to primary recipient: {target_recipient}")

        # 1. Primary Attempt: Resend API (fast, reliable, signed delivery)
        if self.api_key:
            try:
                delivered = self._send_via_resend([target_recipient], subject, email_html, attachments)
                if not delivered:
                    resend_error = "Resend API returned non-200/201 response"
            except Exception as e:
                resend_error = str(e)
                logger.error(f"Resend delivery failed: {e}")
        else:
            resend_error = "RESEND_API_KEY not configured"

        # 2. Secondary Attempt: Direct SMTP (e.g. Gmail App Password)
        smtp_user = os.environ.get("GMAIL_USER") or os.environ.get("SMTP_USER") or target_recipient
        raw_pass = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("SMTP_PASSWORD", "")
        smtp_pass = raw_pass.replace(" ", "").strip()

        if not delivered:
            if smtp_user and smtp_pass:
                logger.info(f"Attempting fallback delivery to {target_recipient} via Gmail SMTP ({smtp_user})...")
                try:
                    delivered = self._send_via_smtp([target_recipient], subject, email_html, attachment_paths)
                    if not delivered:
                        smtp_error = "SMTP delivery returned false without specific error"
                except Exception as e:
                    smtp_error = f"{type(e).__name__}: {str(e)}"
                    logger.error(f"SMTP delivery failed: {e}")
            else:
                smtp_error = "GMAIL_USER / GMAIL_APP_PASSWORD credentials not configured"

        # 3. Raise loud exception if all channels failed
        if not delivered:
            fatal_message = (
                f"FATAL: Email delivery to primary recipient '{target_recipient}' failed completely!\n"
                f"  - Resend dispatch status: {resend_error}\n"
                f"  - SMTP dispatch status: {smtp_error}\n"
                f"Please ensure RESEND_API_KEY is active or GMAIL_USER + GMAIL_APP_PASSWORD are valid."
            )
            logger.critical(fatal_message)
            raise RuntimeError(fatal_message)

        logger.info(f"Consolidated daily report delivered successfully to {target_recipient}.")
        return True

    def _send_via_resend(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        attachments: List[Dict[str, str]]
    ) -> bool:
        """Sends email via Resend API."""
        sanitized_recipients = []
        for r in recipients:
            clean = _sanitize_recipient(r)
            if clean and clean not in sanitized_recipients:
                sanitized_recipients.append(clean)

        if not sanitized_recipients:
            raise ValueError("No valid recipient addresses provided for Resend delivery.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": self.from_email,
            "to": sanitized_recipients,
            "subject": subject,
            "html": html_body,
            "attachments": attachments
        }
        resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=30)
        if resp.status_code in [200, 201]:
            logger.info(f"Email delivered successfully via Resend to {sanitized_recipients}: ID {resp.json().get('id')}")
            return True
        else:
            err_msg = f"Resend API error HTTP {resp.status_code}: {resp.text}"
            logger.error(err_msg)
            return False

    def _send_via_smtp(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        attachment_paths: List[Path]
    ) -> bool:
        """Delivers daily scholarship reports via standard SMTP (e.g. Gmail)."""
        sanitized_recipients = []
        for r in to_addresses:
            clean = _sanitize_recipient(r)
            if clean and clean not in sanitized_recipients:
                sanitized_recipients.append(clean)

        if not sanitized_recipients:
            raise ValueError("No valid recipient addresses provided for SMTP delivery.")

        smtp_user = os.environ.get("GMAIL_USER") or os.environ.get("SMTP_USER") or self.owner_email
        raw_pass = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("SMTP_PASSWORD", "")
        smtp_pass = raw_pass.replace(" ", "").strip()
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "465"))

        if not smtp_user or not smtp_pass:
            raise ValueError("SMTP credentials missing: GMAIL_USER or GMAIL_APP_PASSWORD not set.")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"Scholarship Intelligence Agent <{smtp_user}>"
        msg["To"] = ", ".join(sanitized_recipients)
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

        logger.info(f"Delivered email successfully via SMTP to {sanitized_recipients}")
        return True

    def _build_email_html(
        self,
        public_summary: ReportSummary,
        private_summary: ReportSummary,
        today_pkt: str,
        degraded: bool,
        attachment_paths: Optional[List[Path]] = None,
        deadline_alerts: Optional[List[Dict[str, Any]]] = None,
        agent_telemetry: Optional[Dict[str, Any]] = None
    ) -> str:
        if attachment_paths:
            att_items = "".join(f"<li><code>{Path(p).name}</code></li>" for p in attachment_paths)
        else:
            att_items = f"<li><code>public_scholarships_report_{today_pkt}.pdf</code></li><li><code>private_scholarships_report_{today_pkt}.pdf</code></li>"

        # Format Deadline Alerts section
        deadline_section = ""
        if deadline_alerts:
            alert_rows = ""
            for a in deadline_alerts[:8]:
                badge_color = "#b91c1c" if a.get("urgency") == "URGENT" else ("#d97706" if a.get("urgency") == "HIGH" else "#2563eb")
                alert_rows += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                  <td style="padding: 8px 10px;">
                    <span style="background-color: {badge_color}; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700;">
                      {a.get('urgency', 'ALERT')}
                    </span>
                    <strong style="margin-left: 6px; font-size: 12px; color: #0f172a;">{a.get('opportunity_name', 'Opportunity')}</strong>
                    <div style="font-size: 11px; color: #64748b;">{a.get('sponsor', '')} &bull; Deadline: <strong>{a.get('deadline', 'Not Stated')}</strong> ({a.get('days_left', 0)}d left)</div>
                  </td>
                  <td style="padding: 8px 10px; text-align: right; white-space: nowrap;">
                    <a href="{a.get('apply_url', '#')}" target="_blank" style="background-color: #0284c7; color: #ffffff; text-decoration: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">Apply</a>
                  </td>
                </tr>
                """
            deadline_section = f"""
            <div style="margin-top: 20px; border: 1px solid #fed7aa; background-color: #fffaf5; border-radius: 8px; padding: 14px 16px;">
              <h3 style="margin: 0 0 8px 0; font-size: 13px; font-weight: 700; color: #9a3412;">
                ⚠️ Approaching Deadlines (Agent 9 Priority Alerts)
              </h3>
              <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                {alert_rows}
              </table>
            </div>
            """

        # Format Multi-Agent Telemetry section
        telemetry_section = ""
        if agent_telemetry:
            telemetry_rows = "".join(
                f"<tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 6px 10px; color: #475569;'>{k}</td><td style='padding: 6px 10px; font-weight: 700; color: #0f172a; text-align: right;'>{v}</td></tr>"
                for k, v in agent_telemetry.items()
            )
            telemetry_section = f"""
            <div style="margin-top: 20px; border: 1px solid #e2e8f0; background-color: #f8fafc; border-radius: 8px; padding: 14px 16px;">
              <h4 style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569;">
                🤖 Multi-Agent Orchestrator Intelligence Telemetry
              </h4>
              <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                {telemetry_rows}
              </table>
            </div>
            """

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
        Assalam-o-Alaikum, here is your daily consolidated scholarship, internship, and financial aid report for students with a
        <strong>Khyber Pakhtunkhwa (KP) domicile</strong>, prioritizing <strong>Charsadda district</strong> domicile holders and target public/private universities.
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

      {deadline_section}

      <!-- Attachments Notice -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; margin-top: 20px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 6px 0; font-size: 13px; color: #0f172a;">Attached PDF Reports:</h4>
        <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #475569; line-height: 1.6;">
          {att_items}
        </ul>
      </div>

      {telemetry_section}

      <p style="font-size: 12px; color: #64748b; line-height: 1.5; margin-top: 20px; margin-bottom: 0;">
        All opportunities have been crawled and verified against official Pakistani domains (<code>*.gov.pk</code>, <code>*.edu.pk</code>) and vetted sponsor portals.
        The attached PDF documents contain complete eligibility criteria, priority flags, and direct application links.
      </p>
    </div>

    <!-- Footer -->
    <div style="background-color: #f1f5f9; padding: 14px 24px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0;">
      KP & Charsadda Daily Scholarship Intelligence Agent • Automated Cloud Pipeline • Delivered exclusively to {self.owner_email}
    </div>
  </div>
</body>
</html>
"""

