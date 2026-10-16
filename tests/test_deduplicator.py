import datetime
import pytest
from agent.deduplicator import ScholarshipDeduplicator
from agent.models import ScholarshipRecord


@pytest.fixture
def deduplicator():
    return ScholarshipDeduplicator(fuzzy_threshold=0.88, drop_after_days_unseen=30)


def test_deduplicate_by_apply_url(deduplicator):
    today = datetime.date(2026, 10, 16)
    rec1 = ScholarshipRecord(
        name="HEC Need Based 2026",
        sponsor="HEC",
        apply_url="https://ehsaas.hec.gov.pk/apply",
        award_amount="PKR 50,000",
        source_url="https://hec.gov.pk"
    )
    rec2 = ScholarshipRecord(
        name="HEC Need Based Scholarship Project 2026-27",
        sponsor="Higher Education Commission",
        apply_url="https://ehsaas.hec.gov.pk/apply",
        award_amount="Full Tuition",
        source_url="https://uop.edu.pk/notice"
    )

    merged = deduplicator.deduplicate_and_merge([rec1, rec2], [], today)
    assert len(merged) == 1
    assert "https://hec.gov.pk" in merged[0].all_source_urls
    assert "https://uop.edu.pk/notice" in merged[0].all_source_urls


def test_deduplicate_by_fuzzy_name(deduplicator):
    today = datetime.date(2026, 10, 16)
    rec1 = ScholarshipRecord(
        name="Bacha Khan University Charsadda Financial Aid",
        sponsor="Bacha Khan University Charsadda",
        apply_url="not stated",
        award_amount="100% Tuition",
        source_url="https://bkuc.edu.pk"
    )
    # Very similar name (fuzzy ratio >= 0.88)
    rec2 = ScholarshipRecord(
        name="Bacha Khan University Charsadda Financial Assistance",
        sponsor="Bacha Khan University Charsadda",
        apply_url="not stated",
        award_amount="100% Tuition",
        source_url="https://bkuc.edu.pk/aid"
    )

    merged = deduplicator.deduplicate_and_merge([rec1, rec2], [], today)
    assert len(merged) == 1


def test_drop_after_30_days_unseen(deduplicator):
    today = datetime.date(2026, 10, 16)
    # Stale record last seen 45 days ago
    stale_rec = ScholarshipRecord(
        name="Ancient One-off Grant",
        sponsor="Defunct Donor",
        last_verified="2026-08-01",  # > 30 days ago
        first_seen="2026-08-01"
    )

    # Active historical record last seen 5 days ago
    active_rec = ScholarshipRecord(
        name="Recurring Active Scholarship",
        sponsor="Active Donor",
        last_verified="2026-10-11",  # 5 days ago
        first_seen="2026-09-01"
    )

    merged = deduplicator.deduplicate_and_merge([], [stale_rec, active_rec], today)
    names = [r.name for r in merged]
    assert "Ancient One-off Grant" not in names
    assert "Recurring Active Scholarship" in names
    # Carried-over record should have is_reconfirmed_today = False
    assert merged[0].is_reconfirmed_today is False
