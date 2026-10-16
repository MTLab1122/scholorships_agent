import datetime
import pytest
from agent.normalizer import OpportunityNormalizer
from agent.models import ScholarshipExtractionItem


@pytest.fixture
def normalizer():
    return OpportunityNormalizer(current_cycle="2026-27")


def test_status_closing_soon(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="Urgent Aid",
        sponsor="Test Sponsor",
        deadline="2026-10-20"  # 4 days away
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://uop.edu.pk/sfao", today_date=today, verify_links=False)
    assert rec.status == "Closing soon"
    assert rec.days_left == 4


def test_status_open(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="Long Term Aid",
        sponsor="Test Sponsor",
        deadline="2026-11-30"  # 45 days away
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://hec.gov.pk", today_date=today, verify_links=False)
    assert rec.status == "Open"
    assert rec.days_left == 45


def test_status_rolling(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="Loan Facility",
        sponsor="Ihsan Trust",
        deadline="Rolling / ongoing"
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://ihsantrust.org", today_date=today, verify_links=False)
    assert rec.status == "Rolling / ongoing"
    assert rec.days_left is None


def test_status_deadline_not_stated(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="No Deadline Aid",
        sponsor="Foundation",
        deadline="not stated"
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://example.gov.pk", today_date=today, verify_links=False)
    assert rec.status == "Deadline not stated"


def test_status_closed(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="Past Scheme",
        sponsor="Ministry",
        deadline="2026-10-01"  # 15 days ago
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://example.gov.pk", today_date=today, verify_links=False)
    assert rec.status == "Closed"
    assert rec.days_left == -15


def test_previous_cycle_flagging(normalizer):
    today = datetime.date(2026, 10, 16)
    item = ScholarshipExtractionItem(
        name="Old Scheme Call",
        sponsor="HEC",
        cycle="2024-25",
        deadline="2024-11-15"
    )
    rec = normalizer.normalize_record(item, source_tier=1, source_url="https://hec.gov.pk", today_date=today, verify_links=False)
    assert rec.status == "Previous cycle – awaiting new call"


def test_trust_tier_and_verification_badge(normalizer):
    today = datetime.date(2026, 10, 16)
    # Tier 1 official gov.pk confirmed
    item1 = ScholarshipExtractionItem(
        name="Official Scheme",
        sponsor="HEC",
        confirmed_by_official_source=True
    )
    rec1 = normalizer.normalize_record(item1, source_tier=1, source_url="https://hec.gov.pk/scholarships", today_date=today, verify_links=False)
    assert rec1.source_trust_tier == 1
    assert rec1.verification_badge == "Confirmed"

    # Tier 2 partner republishing
    rec2 = normalizer.normalize_record(item1, source_tier=2, source_url="https://uop.edu.pk/notice/hec", today_date=today, verify_links=False)
    assert rec2.verification_badge == "Confirmed" or rec2.verification_badge == "Via Partner"

    # Tier 3 unverified
    item3 = ScholarshipExtractionItem(
        name="Blog claim",
        sponsor="Unknown",
        confirmed_by_official_source=False
    )
    rec3 = normalizer.normalize_record(item3, source_tier=3, source_url="https://talib.pk/news", today_date=today, verify_links=False)
    assert rec3.verification_badge == "Unverified"
    assert rec3.claimed_by_source == "https://talib.pk/news"
