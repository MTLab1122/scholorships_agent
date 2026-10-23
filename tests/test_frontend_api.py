"""Integration tests for Frontend API endpoints (Admin Control Center & Student Portal)."""
import pytest
from fastapi.testclient import TestClient
from agent.server import app, db
from agent.models import ScholarshipRecord, StudentProfile

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_test_data():
    """Ensure sample opportunity and student exist in the DB for frontend tests."""
    opp = ScholarshipRecord(
        id="test-frontend-opp-1",
        name="Frontend Test Merit Scholarship",
        sponsor="Higher Education Commission",
        sponsor_type="federal govt",
        category="scholarships",
        university_types="both",
        eligible_semesters=[1, 2, 3, 4],
        charsadda_flag=True,
        kp_flag=True,
        deadline="2026-12-31",
        official_url="https://hec.gov.pk/test",
        source_url="https://hec.gov.pk/test",
        verification_badge="Confirmed",
        status="Open"
    )
    db.save_opportunity(opp)

    # Seed test student
    student = StudentProfile(
        id="student-charsadda-cs-01",
        full_name="Muhammad Khan",
        email="student.charsadda@example.com",
        university="Bacha Khan University Charsadda",
        degree_level="Undergraduate",
        discipline="Computer Science",
        current_semester=4,
        cgpa=3.65,
        domicile_district="Charsadda"
    )
    db.save_student(student)
    yield


def test_html_shell_routes():
    """Verify HTML routes serve the integrated application shell."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Student Opportunity Intelligence" in res.text
    assert ("/static/css/tokens.css" in res.text or "_astro" in res.text)
    assert ("/static/js/app.js" in res.text or "_astro" in res.text)

    # Client-side router path fallbacks
    for path in ["/admin/dashboard", "/admin/agents", "/student/dashboard", "/student/opportunities", "/notifications"]:
        r = client.get(path)
        assert r.status_code == 200
        assert "Student Opportunity Intelligence" in r.text


def test_admin_metrics_endpoint():
    """Verify /api/admin/metrics returns real aggregated metrics."""
    res = client.get("/api/admin/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_opportunities" in data
    assert "open_opportunities" in data
    assert "category_distribution" in data
    assert "scope_distribution" in data
    assert data["total_opportunities"] >= 1


def test_admin_agents_endpoints():
    """Verify /api/admin/agents returns all 15 specialized agents and run endpoint works."""
    res = client.get("/api/admin/agents")
    assert res.status_code == 200
    data = res.json()
    assert "agents" in data
    agents = data["agents"]
    assert len(agents) == 15
    agent_ids = [a["id"] for a in agents]
    assert "orchestrator" in agent_ids
    assert "fraud_qc" in agent_ids
    assert "recommendation" in agent_ids

    # Trigger agent run
    run_res = client.post("/api/admin/agents/fraud_qc/run")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "SUCCESS"


def test_admin_sources_endpoints():
    """Verify source registry listing, creation, and connectivity testing."""
    # List sources
    res = client.get("/api/admin/sources")
    assert res.status_code == 200
    assert "sources" in res.json()

    # Add source
    new_source = {
        "name": "Custom Test Portal",
        "url": "https://testportal.edu.pk",
        "category": "university",
        "tier": 1
    }
    create_res = client.post("/api/admin/sources", json=new_source)
    assert create_res.status_code == 200
    assert create_res.json()["status"] == "saved"

    # Test connectivity
    test_res = client.post("/api/admin/sources/test", json={"url": "https://hec.gov.pk"})
    assert test_res.status_code == 200
    assert "status" in test_res.json()


def test_admin_schedules_endpoints():
    """Verify schedules listing and manual trigger."""
    res = client.get("/api/admin/schedules")
    assert res.status_code == 200
    assert "schedules" in res.json()
    schedules = res.json()["schedules"]
    assert len(schedules) >= 5

    # Trigger a schedule
    trig_res = client.post("/api/admin/schedules/SCHED-01/trigger")
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "SUCCESS"


def test_admin_verification_queue():
    """Verify verification queue and review decisions."""
    res = client.get("/api/admin/verification-queue")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Review decision
    rev_res = client.post(
        "/api/admin/verification-queue/test-frontend-opp-1/review",
        json={
            "decision": "approve",
            "reason": "Verified against official gazette notification."
        }
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "SUCCESS"


def test_admin_settings_and_audit():
    """Verify system settings get/save and audit logs."""
    # Get settings
    res = client.get("/api/admin/settings")
    assert res.status_code == 200
    settings = res.json()
    assert "platform_name" in settings

    # Update settings
    save_res = client.post("/api/admin/settings", json={"platform_name": "Student Opportunity Intelligence Pro"})
    assert save_res.status_code == 200
    assert save_res.json()["platform_name"] == "Student Opportunity Intelligence Pro"

    # Audit logs
    audit_res = client.get("/api/admin/audit-logs")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1


def test_global_search():
    """Verify multi-entity search endpoint."""
    res = client.get("/api/search?q=Frontend")
    assert res.status_code == 200
    results = res.json()
    assert "opportunities" in results
    assert len(results["opportunities"]) >= 1
    assert results["opportunities"][0]["name"] == "Frontend Test Merit Scholarship"


def test_notifications_endpoints():
    """Verify notifications listing and mark read endpoints."""
    # Listing
    res = client.get("/api/notifications")
    assert res.status_code == 200
    assert "notifications" in res.json()
    notifs = res.json()["notifications"]
    assert isinstance(notifs, list)

    if notifs:
        first_id = notifs[0]["id"]
        # Mark single read
        r1 = client.post(f"/api/notifications/{first_id}/read")
        assert r1.status_code == 200
        assert r1.json()["success"] is True

    # Mark all read
    r2 = client.post("/api/notifications/mark-all-read", json={})
    assert r2.status_code == 200
    assert "marked_count" in r2.json()


def test_student_saved_endpoints():
    """Verify student profile and bookmark saved opportunity endpoints."""
    # Get student profile
    res = client.get("/api/students/student-charsadda-cs-01")
    assert res.status_code == 200
    assert res.json()["full_name"] == "Muhammad Khan"

    # Toggle bookmark
    toggle_res = client.post(
        "/api/students/student-charsadda-cs-01/saved",
        json={"student_id": "student-charsadda-cs-01", "opportunity_id": "test-frontend-opp-1"}
    )
    assert toggle_res.status_code == 200
    assert "is_saved" in toggle_res.json()

    # List bookmarks
    list_res = client.get("/api/students/student-charsadda-cs-01/saved")
    assert list_res.status_code == 200
    assert isinstance(list_res.json()["saved"], list)
