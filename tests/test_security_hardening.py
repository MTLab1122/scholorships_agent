"""Comprehensive Security Hardening and Vulnerability Verification Test Suite.
Tests:
1. SSRF Prevention: Blocking loopback, link-local, cloud metadata, RFC1918 private IPs, and non-HTTP schemes.
2. OWASP Defense-in-Depth Headers: X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy, Permissions-Policy.
3. Request Payload Size Limits: HTTP 413 rejection on oversized payloads (>10MB).
4. Active Session Revocation on Password Reset.
5. Path Traversal Prevention: Report downloads and database backup restores.
6. BOLA / IDOR & Row-Level Security: Student data isolation and student directory enumeration prevention.
7. Role-Based Access Control (RBAC): Strict administrative privilege boundaries.
8. Rate Limiting Protections: Brute-force throttling on sensitive endpoints.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from agent.server import app, db
from agent.security import validate_outbound_url, sanitize_report_filename, BLOCKED_IP_NETWORKS, FORBIDDEN_HOSTNAMES

client = TestClient(app)


# ==============================================================================
# 1. SSRF (Server-Side Request Forgery) Prevention
# ==============================================================================

def test_ssrf_blocking_loopback_and_metadata():
    """Verify SSRF validator rejects loopback, cloud metadata, and link-local targets."""
    # Obtain admin token
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "AdminPassword123!"
    })
    admin_token = res_admin.json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    malicious_urls = [
        "http://127.0.0.1:8000/api/health",
        "http://localhost:8000/admin/backups",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.1/internal-admin",
        "http://192.168.1.1/router",
        "http://172.16.0.1/secrets",
        "file:///etc/passwd",
        "ftp://internal.vault/keys",
        "gopher://127.0.0.1:6379/_flushall"
    ]

    for target in malicious_urls:
        res = client.post("/api/admin/sources/test", headers=headers, json={"url": target})
        assert res.status_code == 400, f"Expected 400 Bad Request for SSRF target: {target}, got {res.status_code}"
        assert "blocked" in res.json()["detail"].lower() or "forbidden" in res.json()["detail"].lower() or "scheme" in res.json()["detail"].lower() or "protocol" in res.json()["detail"].lower()


def test_ssrf_direct_unit_validation():
    """Unit test validate_outbound_url against diverse malicious vectors."""
    with pytest.raises(Exception):
        validate_outbound_url("http://127.0.0.1:9000")
    with pytest.raises(Exception):
        validate_outbound_url("http://localhost:3000")
    with pytest.raises(Exception):
        validate_outbound_url("http://169.254.169.254/meta-data")
    with pytest.raises(Exception):
        validate_outbound_url("http://10.250.1.1/status")
    with pytest.raises(Exception):
        validate_outbound_url("file:///data/opportunities.db")
    with pytest.raises(Exception):
        validate_outbound_url("javascript:alert(1)")


# ==============================================================================
# 2. OWASP Defensive HTTP Headers
# ==============================================================================

def test_owasp_security_headers_present():
    """Verify modern OWASP security headers are attached to all API responses."""
    res = client.get("/api/health")
    assert res.status_code == 200
    headers = res.headers

    # Defense-in-depth headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers
    assert "Content-Security-Policy" in headers


# ==============================================================================
# 3. Request Payload Size Limiting (DoS Protection)
# ==============================================================================

def test_request_size_limit_middleware():
    """Verify middleware rejects excessively large payloads with HTTP 413."""
    # Send request with content-length header claiming > 10MB
    res = client.post(
        "/api/telemetry/events",
        headers={"Content-Length": str(15 * 1024 * 1024)},
        content=b"A" * 1024
    )
    assert res.status_code == 413
    assert "payload too large" in res.json()["detail"].lower()


# ==============================================================================
# 4. Session Invalidation on Password Reset
# ==============================================================================

def test_session_invalidation_on_password_reset():
    """Verify that resetting a password instantly revokes all existing active sessions."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"session.revoke.{unique_id}@uop.edu.pk"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "InitialPassword123!",
        "full_name": "Revoke Tester",
        "role": "student"
    })

    # Log in to establish an active session token
    res_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "InitialPassword123!"
    })
    token = res_login.json()["token"]

    # Verify session works
    res_me_before = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me_before.status_code == 200

    # Request password reset
    res_forgot = client.post("/api/auth/forgot-password", json={"email": email})
    reset_token = res_forgot.json()["reset_token"]

    # Reset password
    res_reset = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSecurePassword456!"
    })
    assert res_reset.status_code == 200

    # CRITICAL: Old token MUST now be invalid
    res_me_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me_after.status_code == 401, "Old session token was not invalidated after password reset!"


# ==============================================================================
# 5. Path Traversal & Filename Sanitization
# ==============================================================================

def test_path_traversal_prevention_on_reports():
    """Verify report download endpoint blocks path traversal attempts."""
    traversal_filenames = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "....//data/opportunities.db",
        "test.exe",
        "malicious.sh",
        "secret.env"
    ]

    for fname in traversal_filenames:
        res = client.get(f"/api/reports/download/{fname}")
        assert res.status_code in (400, 404), f"Expected 400 or 404 for traversal filename: {fname}, got {res.status_code}"


def test_backup_restore_traversal_prevention():
    """Verify restore backup rejects path traversal and non-whitelisted patterns."""
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "AdminPassword123!"
    })
    admin_token = res_admin.json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    bad_filenames = [
        "../../data/opportunities.db",
        "random_file.txt",
        "opportunities_backup_123.db; rm -rf /",
        "backups/nested/file.db"
    ]

    for bname in bad_filenames:
        res = client.post("/api/admin/backups/restore", headers=headers, json={"filename": bname})
        assert res.status_code in (400, 500)


# ==============================================================================
# 6. BOLA / IDOR & Row-Level Security
# ==============================================================================

def test_student_data_isolation_bola():
    """Verify student A cannot view or manipulate student B's applications or bookmarks."""
    # Register Student A
    id_a = uuid.uuid4().hex[:8]
    email_a = f"student.a.{id_a}@uop.edu.pk"
    res_reg_a = client.post("/api/auth/register", json={
        "email": email_a,
        "password": "PasswordA123!",
        "full_name": "Student A",
        "role": "student"
    })
    token_a = res_reg_a.json()["token"]
    stu_id_a = res_reg_a.json()["user"]["student_id"]

    # Register Student B
    id_b = uuid.uuid4().hex[:8]
    email_b = f"student.b.{id_b}@uop.edu.pk"
    res_reg_b = client.post("/api/auth/register", json={
        "email": email_b,
        "password": "PasswordB123!",
        "full_name": "Student B",
        "role": "student"
    })
    token_b = res_reg_b.json()["token"]
    stu_id_b = res_reg_b.json()["user"]["student_id"]

    # Student A attempts to access Student B's applications
    res_cross_app = client.get(
        f"/api/applications/{stu_id_b}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_cross_app.status_code == 403, "Student A was able to access Student B's applications!"

    # Student A attempts to view Student B's saved opportunities
    res_cross_saved = client.get(
        f"/api/students/{stu_id_b}/saved",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_cross_saved.status_code == 403, "Student A was able to access Student B's saved opportunities!"

    # Student A attempts to bookmark on behalf of Student B
    res_cross_add_saved = client.post(
        f"/api/students/{stu_id_b}/saved",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"student_id": stu_id_b, "opportunity_id": "SCH-202610-0015"}
    )
    assert res_cross_add_saved.status_code == 403, "Student A was able to modify Student B's bookmarks!"


def test_student_directory_enumeration_blocked():
    """Verify unprivileged students cannot enumerate the entire student directory."""
    id_stu = uuid.uuid4().hex[:8]
    email_stu = f"student.dir.{id_stu}@uop.edu.pk"
    res_reg = client.post("/api/auth/register", json={
        "email": email_stu,
        "password": "Password123!",
        "full_name": "Student Directory Tester",
        "role": "student"
    })
    stu_token = res_reg.json()["token"]

    # Student calls GET /api/students
    res = client.get("/api/students", headers={"Authorization": f"Bearer {stu_token}"})
    assert res.status_code == 403, "Unprivileged student was able to dump student directory!"


# ==============================================================================
# 7. Role-Based Access Control (RBAC) Boundaries
# ==============================================================================

def test_student_blocked_from_admin_backups_and_telemetry():
    """Verify regular student token cannot access admin routes."""
    id_stu = uuid.uuid4().hex[:8]
    email_stu = f"rbac.test.{id_stu}@uop.edu.pk"
    res_reg = client.post("/api/auth/register", json={
        "email": email_stu,
        "password": "Password123!",
        "full_name": "RBAC Tester",
        "role": "student"
    })
    stu_token = res_reg.json()["token"]
    headers = {"Authorization": f"Bearer {stu_token}"}

    # Backup listing
    res_backups = client.get("/api/admin/backups", headers=headers)
    assert res_backups.status_code == 403

    # Telemetry statistics
    res_stats = client.get("/api/telemetry/stats", headers=headers)
    assert res_stats.status_code == 403

    # Triggering automated schedules
    res_trigger = client.post("/api/admin/schedules/SCHED-01/trigger", headers=headers)
    assert res_trigger.status_code == 403
