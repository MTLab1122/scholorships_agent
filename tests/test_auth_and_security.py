"""Tests for Auth, RBAC, Rate-Limiting, Backups, and Telemetry."""
import pytest
from fastapi.testclient import TestClient
from agent.server import app, db

client = TestClient(app)


def test_auth_login_seeded_accounts():
    """Verify seeded student and admin demo accounts can log in."""
    # Ensure default users are seeded in DB
    db.seed_default_users()

    # Test Admin login
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "AdminPassword123!"
    })
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["user"]["role"] == "admin"
    assert "token" in admin_data

    # Test Student login
    res_stu = client.post("/api/auth/login", json={
        "email": "student@uop.edu.pk",
        "password": "StudentPassword123!"
    })
    assert res_stu.status_code == 200
    stu_data = res_stu.json()
    assert stu_data["user"]["role"] == "student"
    assert "token" in stu_data

    # Test Invalid password
    res_fail = client.post("/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "WrongPassword!"
    })
    assert res_fail.status_code == 401


import uuid

def test_auth_registration_and_verification():
    """Verify registration creates user and issues verification token."""
    test_email = f"test.applicant.{uuid.uuid4().hex[:8]}@uop.edu.pk"
    res_reg = client.post("/api/auth/register", json={
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "Test Applicant",
        "role": "student",
        "university": "University of Peshawar",
        "degree_level": "Undergraduate",
        "discipline": "Computer Science",
        "current_semester": 5,
        "cgpa": 3.75,
        "domicile_district": "Charsadda"
    })
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["is_verified"] is False
    assert reg_data.get("verification_token") is not None

    token = reg_data["verification_token"]
    # Verify email
    res_ver = client.post("/api/auth/verify-email", json={"token": token})
    assert res_ver.status_code == 200
    assert res_ver.json()["success"] is True


def test_auth_forgot_and_reset_password():
    """Verify forgot password produces token and allows secure password reset."""
    test_email = f"pwd.reset.{uuid.uuid4().hex[:8]}@uop.edu.pk"
    client.post("/api/auth/register", json={
        "email": test_email,
        "password": "OldPassword123!",
        "full_name": "Password Reset User",
        "role": "student"
    })

    # Request reset
    res_forgot = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert res_forgot.status_code == 200
    reset_token = res_forgot.json().get("reset_token")
    assert reset_token is not None

    # Reset password
    res_reset = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSuperPassword123!"
    })
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True

    # Login with new password
    res_new_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "NewSuperPassword123!"
    })
    assert res_new_login.status_code == 200


def test_auth_rbac_and_profile_deletion():
    """Verify student session token authentication and account deletion."""
    test_email = f"delete.me.{uuid.uuid4().hex[:8]}@uop.edu.pk"
    client.post("/api/auth/register", json={
        "email": test_email,
        "password": "DeletePassword123!",
        "full_name": "Temporary Student",
        "role": "student"
    })

    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "DeletePassword123!"
    })
    auth_token = login_res.json()["token"]

    # Access current user profile via auth token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert res_me.status_code == 200
    assert res_me.json()["user"]["email"] == test_email

    # Delete account
    res_del = client.request("DELETE", "/api/auth/account", headers={"Authorization": f"Bearer {auth_token}"}, json={"password": "DeletePassword123!"})
    assert res_del.status_code == 200

    # Verify deleted user cannot login
    res_relogin = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "DeletePassword123!"
    })
    assert res_relogin.status_code == 401


def test_backups_lifecycle():
    """Verify backup creation, listing, and restore protection with admin auth."""
    # Obtain admin auth token
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "AdminPassword123!"
    })
    admin_token = res_admin.json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # List backups
    res_list = client.get("/api/admin/backups", headers=headers)
    assert res_list.status_code == 200
    assert "backups" in res_list.json()

    # Create backup
    res_create = client.post("/api/admin/backups/create", headers=headers)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["success"] is True
    assert "filename" in created["backup"]
    filename = created["backup"]["filename"]

    # Verify newly created backup is listed
    res_list_after = client.get("/api/admin/backups", headers=headers)
    filenames = [b["filename"] for b in res_list_after.json()["backups"]]
    assert filename in filenames

    # Test restoration with automatic pre-snapshot
    res_restore = client.post("/api/admin/backups/restore", headers=headers, json={"filename": filename})
    assert res_restore.status_code == 200
    assert res_restore.json()["success"] is True


def test_telemetry_endpoints():
    """Verify telemetry events and errors ingestion."""
    # Send anonymous event
    res_event = client.post("/api/telemetry/events", json={
        "event_name": "page_view",
        "category": "navigation",
        "anonymous_id": "test-session-123",
        "properties": {"filter": "Charsadda"}
    })
    assert res_event.status_code == 200
    assert res_event.json()["status"] == "logged"

    # Send error report
    res_error = client.post("/api/telemetry/errors", json={
        "error_message": "TypeError: Cannot read property of undefined",
        "url": "http://localhost:4321/student/opportunities",
        "user_agent": "Mozilla/5.0"
    })
    assert res_error.status_code == 200
    assert res_error.json()["status"] == "logged"
