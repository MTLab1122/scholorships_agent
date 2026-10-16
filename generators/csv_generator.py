"""CSV Report Generator for Scholarship Records.
Outputs all required fields from Section 7 and Section 5 in standard UTF-8 CSV format.
"""

import csv
import io
from pathlib import Path
from typing import List, Union
from agent.models import ScholarshipRecord

CSV_FIELDNAMES = [
    "id",
    "name",
    "sponsor",
    "sponsor_type",
    "university_types",
    "eligible_institutions",
    "degree_levels",
    "fields_of_study",
    "academic_years",
    "domicile_requirements",
    "district_requirements",
    "other_geographic",
    "kp_eligibility",
    "charsadda_eligibility",
    "merit_criteria",
    "need_criteria",
    "min_gpa_or_marks",
    "income_cap",
    "age_limit",
    "gender",
    "other_conditions",
    "award_amount",
    "benefits",
    "duration",
    "number_of_awards",
    "application_procedure",
    "required_documents",
    "attestation_requirements",
    "apply_url",
    "opening_date",
    "deadline",
    "document_upload_deadline",
    "expiry_date",
    "cycle",
    "contact_email",
    "contact_phone",
    "contact_address",
    "source_url",
    "evidence_quote",
    "confirmed_by_official_source",
    "charsadda_flag",
    "kp_flag",
    "pakistan_wide_kp_eligible",
    "target_uni_flag",
    "merged_districts_only",
    "status",
    "days_left",
    "source_trust_tier",
    "verification_badge",
    "link_status_apply",
    "link_status_source",
    "first_seen",
    "last_verified",
]


class CSVReportGenerator:
    def __init__(self):
        pass

    def generate_csv(self, records: List[ScholarshipRecord], output_path: Union[str, Path]) -> None:
        """Writes records to a CSV file with utf-8-sig (Excel friendly) encoding."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                row = r.model_dump()
                writer.writerow(row)

    def generate_csv_string(self, records: List[ScholarshipRecord]) -> str:
        """Returns CSV content as string."""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r.model_dump())
        return buf.getvalue()
