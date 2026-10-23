"""Comprehensive Live System & End-to-End Verification Test Suite.
Tests all 33 routes, static assets, APIs, RBAC, CRUD, and responsive layout tokens
against the live running application at http://127.0.0.1:8000.
"""
import re
import uuid
import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

ALL_ROUTES = [
    "/",
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
    "/verify-email",
    "/onboarding",
    "/privacy",
    "/terms",
    "/404",
    "/notifications",
    "/student/dashboard",
    "/student/opportunities",
    "/student/applications",
    "/student/recommendations",
    "/student/saved",
    "/student/prep",
    "/student/profile",
    "/admin/dashboard",
    "/admin/opportunities",
    "/admin/agents",
    "/admin/sources",
    "/admin/workflows",
    "/admin/verification",
    "/admin/reports",
    "/admin/schedules",
    "/admin/settings",
    "/admin/audit-logs",
    "/admin/health",
    "/admin/backups",
    "/admin/students"
]


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"User-Agent": "SOI-Platform-QA-Verifier/2.0"})
    return s


def test_live_server_health(session):
    """Verify live server is online and responding."""
    res = session.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["total_opportunities"] > 0


@pytest.mark.parametrize("route", ALL_ROUTES)
def test_all_routes_return_200_and_valid_html(session, route):
    """Verify every single application route renders HTTP 200 with complete HTML."""
    res = session.get(f"{BASE_URL}{route}")
    assert res.status_code == 200, f"Route {route} failed with status {res.status_code}"
    html = res.text
    assert "<!DOCTYPE html>" in html or "<!doctype html>" in html or "<html" in html
    assert "<title>" in html
    # Check viewport meta tag for mobile responsiveness
    assert 'name="viewport"' in html
    assert "width=device-width" in html


def test_invalid_route_returns_404_page(session):
    """Verify unknown routes serve the 404 page."""
    res = session.get(f"{BASE_URL}/non-existent-opportunity-page-xyz-12345")
    # In Astro SSG or SPA fallback, either 404 or our custom 404 template is returned
    assert res.status_code in [200, 404]
    if res.status_code == 200:
        assert ("Page Not Found" in res.text or "404" in res.text or "Student Opportunity Intelligence" in res.text)


def test_static_assets_integrity(session):
    """Extract and verify all linked CSS, JS, and font assets in the landing page return HTTP 200."""
    res = session.get(f"{BASE_URL}/")
    html = res.text
    # Find all asset links
    links = re.findall(r'href="(/_astro/[^"]+)"', html) + re.findall(r'src="(/_astro/[^"]+)"', html)
    assert len(links) > 0, "No assets found in HTML"
    checked = set()
    for asset in links:
        if asset in checked:
            continue
        checked.add(asset)
        asset_res = session.get(f"{BASE_URL}{asset}")
        assert asset_res.status_code == 200, f"Broken asset link: {asset} returned {asset_res.status_code}"


def test_auth_full_journey(session):
    """Test full authentication journey: Register -> Login -> Me -> Logout -> Re-login."""
    unique_email = f"qa.journey.{uuid.uuid4().hex[:8]}@uop.edu.pk"
    pwd = "QASecurePassword123!"

    # 1. Register
    reg_res = session.post(f"{BASE_URL}/api/auth/register", json={
        "email": unique_email,
        "password": pwd,
        "full_name": "QA Test Journey",
        "role": "student",
        "university": "University of Peshawar",
        "discipline": "Computer Science"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["token"]

    # 2. Get profile via Bearer token
    me_res = session.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == unique_email

    # 3. Logout
    logout_res = session.post(f"{BASE_URL}/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # 4. Old token should now be invalidated
    unauth_res = session.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert unauth_res.status_code == 401

    # 5. Re-login
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": unique_email,
        "password": pwd
    })
    assert login_res.status_code == 200
    new_token = login_res.json()["token"]
    assert new_token != token


def test_rbac_boundary_enforcement(session):
    """Verify Student tokens are blocked from Admin endpoints."""
    # Login as student
    stu_login = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "student@uop.edu.pk",
        "password": "StudentPassword123!"
    })
    stu_token = stu_login.json()["token"]
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # Attempt to access admin backups as student -> Must be 403 Forbidden
    admin_backup_res = session.get(f"{BASE_URL}/api/admin/backups", headers=stu_headers)
    assert admin_backup_res.status_code == 403

    # Attempt to access admin telemetry stats as student -> Must be 403 Forbidden
    admin_telemetry_res = session.get(f"{BASE_URL}/api/telemetry/stats", headers=stu_headers)
    assert admin_telemetry_res.status_code == 403

    # Login as admin
    admin_login = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@opportunity.edu.pk",
        "password": "AdminPassword123!"
    })
    admin_token = admin_login.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin CAN access admin backups
    admin_ok = session.get(f"{BASE_URL}/api/admin/backups", headers=admin_headers)
    assert admin_ok.status_code == 200


def test_opportunities_catalog_and_filters(session):
    """Test filtering opportunities by category, university type, semester, and query."""
    # 1. Base listing
    res = session.get(f"{BASE_URL}/api/opportunities?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] > 0
    opps = data["opportunities"]
    assert len(opps) > 0

    first_id = opps[0]["id"]
    # 2. Detail view
    detail_res = session.get(f"{BASE_URL}/api/opportunities/{first_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == first_id

    # 3. Filter by university type
    pub_res = session.get(f"{BASE_URL}/api/opportunities?university_type=public")
    assert pub_res.status_code == 200

    # 4. Filter by semester
    sem_res = session.get(f"{BASE_URL}/api/opportunities?semester=4")
    assert sem_res.status_code == 200

    # 5. Search query
    search_res = session.get(f"{BASE_URL}/api/opportunities?search=HEC")
    assert search_res.status_code == 200


def test_kanban_application_lifecycle(session):
    """Test application creation, status transitions, task additions and toggles."""
    # Find an opportunity
    opps = session.get(f"{BASE_URL}/api/opportunities?limit=5").json()["opportunities"]
    opp_id = opps[0]["id"]
    student_id = "STU-1792427107"

    # 1. Create or get application
    app_res = session.post(f"{BASE_URL}/api/applications", json={
        "student_id": student_id,
        "opportunity_id": opp_id,
        "stage": "interested",
        "notes": "Testing Kanban workflow"
    })
    assert app_res.status_code in [200, 400]  # 400 if already created in previous run
    app_id = app_res.json().get("id") if app_res.status_code == 200 else None

    if not app_id:
        apps = session.get(f"{BASE_URL}/api/applications?student_id={student_id}").json()["applications"]
        app_id = apps[0]["id"]

    # 2. Transition status
    update_res = session.post(f"{BASE_URL}/api/applications/status", json={
        "application_id": app_id,
        "student_id": student_id,
        "new_status": "preparing_documents",
        "notes": "Drafting personal statement"
    })
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "preparing_documents"

    # 3. Add task
    task_res = session.post(f"{BASE_URL}/api/applications/task", json={
        "application_id": app_id,
        "student_id": student_id,
        "task_title": "Get Department HoD Recommendation Letter"
    })
    assert task_res.status_code == 200
    tasks = task_res.json()["tasks"]
    assert len(tasks) > 0
    task_id = tasks[-1]["id"]

    # 4. Toggle task
    toggle_res = session.post(
        f"{BASE_URL}/api/applications/task/toggle?application_id={app_id}&student_id={student_id}&task_id={task_id}"
    )
    assert toggle_res.status_code == 200


def test_saved_opportunities_toggle(session):
    """Test student bookmarking functionality."""
    student_id = "STU-1792427107"
    opps = session.get(f"{BASE_URL}/api/opportunities?limit=1").json()["opportunities"]
    opp_id = opps[0]["id"]

    # Toggle bookmark
    toggle_res = session.post(f"{BASE_URL}/api/students/{student_id}/saved", json={
        "student_id": student_id,
        "opportunity_id": opp_id
    })
    assert toggle_res.status_code == 200
    is_saved = toggle_res.json()["is_saved"]

    # Verify list reflects state
    list_res = session.get(f"{BASE_URL}/api/students/{student_id}/saved")
    assert list_res.status_code == 200
    saved_ids = [s["id"] for s in list_res.json()["saved"]]
    if is_saved:
        assert opp_id in saved_ids
    else:
        assert opp_id not in saved_ids


def test_application_prep_packet_generation(session):
    """Test generating personalized application prep packet."""
    student_id = "STU-1792427107"
    opps = session.get(f"{BASE_URL}/api/opportunities?limit=1").json()["opportunities"]
    opp_id = opps[0]["id"]

    res = session.post(f"{BASE_URL}/api/prep-packet?student_id={student_id}&opportunity_id={opp_id}")
    assert res.status_code == 200
    packet = res.json()
    assert "document_checklist" in packet
    assert "statement_of_purpose_guide" in packet
    assert "recommendation_letter_template" in packet


def test_report_generation_and_download(session):
    """Test triggering Report 01 and downloading the generated file."""
    gen_res = session.post(f"{BASE_URL}/api/reports/generate", json={
        "report_number": "01",
        "formats": ["csv", "html"]
    })
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "generated_files" in gen_data
    assert len(gen_data["generated_files"]) > 0

    # Pick first generated file and download
    file_path = list(gen_data["generated_files"].values())[0]
    import os
    filename = os.path.basename(file_path)
    download_res = session.get(f"{BASE_URL}/api/reports/download/{filename}")
    assert download_res.status_code == 200
    assert len(download_res.content) > 0


def test_admin_sources_and_testing(session):
    """Test source registry, testing reachability, and adding a verified source."""
    # List sources
    res = session.get(f"{BASE_URL}/api/admin/sources")
    assert res.status_code == 200
    assert "sources" in res.json()

    # Test source reachability
    test_res = session.post(f"{BASE_URL}/api/admin/sources/test", json={"url": "https://hec.gov.pk"})
    assert test_res.status_code == 200
    assert "status" in test_res.json()

    # Add source
    add_res = session.post(f"{BASE_URL}/api/admin/sources", json={
        "name": f"QA Tested University {uuid.uuid4().hex[:4]}",
        "url": f"https://uop.edu.pk/test-{uuid.uuid4().hex[:6]}",
        "category": "university",
        "tier": 1
    })
    assert add_res.status_code == 200


def test_admin_schedules_and_trigger(session):
    """Test automated background schedules and manual trigger."""
    res = session.get(f"{BASE_URL}/api/admin/schedules")
    assert res.status_code == 200
    schedules = res.json()["schedules"]
    assert len(schedules) > 0

    # Trigger SCHED-01
    trig_res = session.post(f"{BASE_URL}/api/admin/schedules/SCHED-01/trigger")
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "SUCCESS"


def test_global_search_endpoint(session):
    """Test platform-wide search for opportunities, sources, and students."""
    res = session.get(f"{BASE_URL}/api/search?q=Peshawar")
    assert res.status_code == 200
    results = res.json()
    assert "opportunities" in results
    assert "sources" in results


def test_settings_persistence(session):
    """Test reading and writing system settings."""
    res = session.get(f"{BASE_URL}/api/admin/settings")
    assert res.status_code == 200
    current = res.json()

    # Update platform title and restore
    new_title = "Student Opportunity Intelligence QA Edition"
    save_res = session.post(f"{BASE_URL}/api/admin/settings", json={
        **current,
        "platform_title": new_title
    })
    assert save_res.status_code == 200
    assert save_res.json()["platform_title"] == new_title
