"""Database layer for Student Opportunity Intelligence Platform.
Uses SQLite for robust, zero-dependency, local transactional persistence.
Includes schema migration, change history tracking, source registry,
student profiles, application tracking, matches, notifications, and job telemetry.
Fully synchronizes with and preserves existing data/scholarships.json.
"""

import os
import re
import json
import uuid
import sqlite3
import hashlib
import secrets
import shutil
from datetime import datetime, timezone, timedelta, date
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "opportunities.db"
DEFAULT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "scholarships.json"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.seed_default_users()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and migrations if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Opportunities table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sponsor TEXT NOT NULL,
                sponsor_type TEXT DEFAULT 'other',
                category TEXT DEFAULT 'scholarships',
                university_types TEXT DEFAULT 'not stated',
                eligible_institutions TEXT DEFAULT 'not stated',
                degree_levels TEXT DEFAULT 'not stated',
                fields_of_study TEXT DEFAULT 'not stated',
                academic_years TEXT DEFAULT 'not stated',
                domicile_requirements TEXT DEFAULT 'not stated',
                district_requirements TEXT DEFAULT 'not stated',
                other_geographic TEXT DEFAULT 'not stated',
                kp_eligibility TEXT DEFAULT 'not stated',
                charsadda_eligibility TEXT DEFAULT 'not stated',
                merit_criteria TEXT DEFAULT 'not stated',
                need_criteria TEXT DEFAULT 'not stated',
                min_gpa_or_marks TEXT DEFAULT 'not stated',
                income_cap TEXT DEFAULT 'not stated',
                age_limit TEXT DEFAULT 'not stated',
                gender TEXT DEFAULT 'not stated',
                other_conditions TEXT DEFAULT 'not stated',
                award_amount TEXT DEFAULT 'not stated',
                benefits TEXT DEFAULT 'not stated',
                duration TEXT DEFAULT 'not stated',
                number_of_awards TEXT DEFAULT 'not stated',
                application_procedure TEXT DEFAULT 'not stated',
                required_documents TEXT DEFAULT 'not stated',
                attestation_requirements TEXT DEFAULT 'not stated',
                apply_url TEXT DEFAULT 'not stated',
                opening_date TEXT DEFAULT 'not stated',
                deadline TEXT DEFAULT 'not stated',
                document_upload_deadline TEXT DEFAULT 'not stated',
                expiry_date TEXT DEFAULT 'not stated',
                cycle TEXT DEFAULT 'not stated',
                contact_email TEXT DEFAULT 'not stated',
                contact_phone TEXT DEFAULT 'not stated',
                contact_address TEXT DEFAULT 'not stated',
                source_url TEXT DEFAULT 'not stated',
                evidence_quote TEXT DEFAULT 'not stated',
                confirmed_by_official_source INTEGER DEFAULT 0,
                charsadda_flag INTEGER DEFAULT 0,
                kp_flag INTEGER DEFAULT 0,
                pakistan_wide_kp_eligible INTEGER DEFAULT 0,
                target_uni_flag INTEGER DEFAULT 0,
                merged_districts_only INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Deadline not stated',
                days_left INTEGER,
                source_trust_tier INTEGER DEFAULT 1,
                verification_badge TEXT DEFAULT 'Unverified',
                claimed_by_source TEXT,
                link_status_apply TEXT DEFAULT 'not stated',
                link_status_source TEXT DEFAULT 'not stated',
                first_seen TEXT,
                last_verified TEXT,
                is_reconfirmed_today INTEGER DEFAULT 1,
                all_source_urls TEXT DEFAULT '[]',
                notes TEXT,
                is_national INTEGER DEFAULT 1,
                is_international INTEGER DEFAULT 0,
                work_mode TEXT DEFAULT 'not stated',
                paid_status TEXT DEFAULT 'not stated',
                stipend_amount TEXT DEFAULT 'not stated',
                eligible_semesters TEXT DEFAULT '[]',
                is_fully_funded INTEGER DEFAULT 0,
                is_partially_funded INTEGER DEFAULT 0,
                is_need_based INTEGER DEFAULT 0,
                is_merit_based INTEGER DEFAULT 0,
                fraud_risk_score REAL DEFAULT 0.0,
                fraud_risk_flags TEXT DEFAULT '[]',
                raw_json TEXT
            );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_category ON opportunities(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_deadline ON opportunities(deadline);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_flags ON opportunities(charsadda_flag, kp_flag, target_uni_flag);")

            # 2. Opportunity Changes History
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunity_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                detected_at TEXT NOT NULL,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_change_opp ON opportunity_changes(opportunity_id);")

            # 3. Source Registry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                url TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tier INTEGER DEFAULT 1,
                category TEXT DEFAULT 'general',
                status TEXT DEFAULT 'active',
                last_checked TEXT,
                last_success TEXT,
                consecutive_failures INTEGER DEFAULT 0,
                items_discovered INTEGER DEFAULT 0,
                error_message TEXT
            );
            """)

            # 4. Student Profiles
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT DEFAULT '',
                university TEXT NOT NULL,
                university_type TEXT DEFAULT 'public',
                degree_level TEXT DEFAULT 'Undergraduate',
                discipline TEXT NOT NULL,
                current_semester INTEGER DEFAULT 1,
                cgpa REAL DEFAULT 3.0,
                domicile_district TEXT DEFAULT 'Charsadda',
                domicile_province TEXT DEFAULT 'Khyber Pakhtunkhwa',
                work_preference TEXT DEFAULT 'any',
                funding_need TEXT DEFAULT 'any',
                skills TEXT DEFAULT '[]',
                interests TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 5. Student Opportunity Matches
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                match_score REAL NOT NULL,
                eligibility_status TEXT NOT NULL,
                reasons TEXT DEFAULT '[]',
                unmet_criteria TEXT DEFAULT '[]',
                unknown_criteria TEXT DEFAULT '[]',
                recommended_priority TEXT DEFAULT 'medium',
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, opportunity_id),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_student ON student_matches(student_id);")

            # 6. Applications & Tracking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                status TEXT DEFAULT 'interested',
                deadline TEXT,
                notes TEXT DEFAULT '',
                tasks_json TEXT DEFAULT '[]',
                documents_checklist_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(student_id, opportunity_id),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_student ON applications(student_id);")

            # 7. Notifications
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                opportunity_id TEXT,
                channel TEXT DEFAULT 'in_app',
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'deadline',
                sent_at TEXT NOT NULL,
                read_at TEXT,
                dedup_key TEXT UNIQUE
            );
            """)

            # 8. Agent Execution Jobs & Telemetry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_jobs (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                run_type TEXT DEFAULT 'manual',
                status TEXT DEFAULT 'completed',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                items_discovered INTEGER DEFAULT 0,
                items_extracted INTEGER DEFAULT 0,
                items_verified INTEGER DEFAULT 0,
                errors_json TEXT DEFAULT '[]',
                tokens_used INTEGER DEFAULT 0,
                cost_estimate_usd REAL DEFAULT 0.0,
                log_summary TEXT DEFAULT ''
            );
            """)

            # 9. Reports History
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports_history (
                id TEXT PRIMARY KEY,
                report_number TEXT NOT NULL,
                report_title TEXT NOT NULL,
                category TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                total_records INTEGER DEFAULT 0,
                file_paths_json TEXT DEFAULT '{}',
                filters_json TEXT DEFAULT '{}'
            );
            """)

            # 10. Admin Audit Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                created_at TEXT NOT NULL
            );
            """)

            # 11. Saved Opportunities Bookmarks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_opportunities (
                student_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                PRIMARY KEY (student_id, opportunity_id),
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            );
            """)

            # 12. System Settings Key-Value Store
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 13. Users & Authentication
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                full_name TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expires TEXT,
                student_id TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_vtoken ON users(verification_token);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_rtoken ON users(reset_token);")

            # 14. Sessions & Auth Tokens
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                student_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_uid ON sessions(user_id);")

            # 15. Privacy-Conscious Analytics & Telemetry Events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                category TEXT NOT NULL,
                properties_json TEXT DEFAULT '{}',
                anonymous_id TEXT,
                user_id TEXT,
                timestamp TEXT NOT NULL
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_ev ON analytics_events(event_name);")

            # 16. Frontend Exceptions & Error Tracking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS frontend_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                url TEXT,
                user_agent TEXT,
                user_id TEXT,
                created_at TEXT NOT NULL
            );
            """)

            conn.commit()

    def sync_from_json(self, json_path: Optional[Path] = None) -> int:
        """Imports or updates opportunities from scholarships.json into SQLite."""
        p = json_path or DEFAULT_JSON_PATH
        if not p.exists():
            return 0
        try:
            with open(p, "r", encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                return 0

            count = 0
            for r in records:
                self.save_opportunity(r)
                count += 1
            logger.info(f"Synchronized {count} records from {p} into database.")
            return count
        except Exception as e:
            logger.error(f"Error importing from JSON {p}: {e}")
            return 0

    def sync_to_json(self, json_path: Optional[Path] = None) -> int:
        """Exports all active opportunities from SQLite back into scholarships.json."""
        p = json_path or DEFAULT_JSON_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        records = self.get_all_opportunities()
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(records)} opportunities from DB to {p}.")
            return len(records)
        except Exception as e:
            logger.error(f"Error exporting DB to JSON {p}: {e}")
            return 0

    def save_opportunity(self, opp: Any) -> str:
        """Inserts or updates an opportunity and records change history."""
        if hasattr(opp, "model_dump"):
            opp = opp.model_dump()
        elif hasattr(opp, "dict"):
            opp = opp.dict()
        opp_id = opp.get("id") or f"OPP-{date.today().strftime('%Y%m')}-{hash(opp.get('name', '')) % 10000:04d}"
        opp["id"] = opp_id

        # Defaults and category inference if missing
        category = opp.get("category")
        if not category or category == "scholarship":
            category = "scholarships"
        name_lower = opp.get("name", "").lower()
        if not opp.get("category"):
            if "internship" in name_lower or "trainee" in name_lower or "fellow" in name_lower:
                category = "internships"
            elif "fellowship" in name_lower or "research" in name_lower:
                category = "research_fellowships"
            elif "competition" in name_lower or "hackathon" in name_lower:
                category = "competitions_hackathons"

        # Check existing for change detection
        existing = self.get_opportunity(opp_id)
        now_str = datetime.now().isoformat()

        if existing:
            # Detect changes in material fields
            for field in ["deadline", "award_amount", "status", "apply_url", "min_gpa_or_marks"]:
                old_val = str(existing.get(field, ""))
                new_val = str(opp.get(field, ""))
                if old_val and new_val and old_val != new_val and old_val != "not stated":
                    self.record_change(opp_id, f"{field}_changed", field, old_val, new_val, now_str)

        all_urls = opp.get("all_source_urls", [])
        if isinstance(all_urls, list):
            all_urls_json = json.dumps(all_urls)
        else:
            all_urls_json = "[]"

        semesters = opp.get("eligible_semesters", [])
        if isinstance(semesters, list):
            semesters_json = json.dumps(semesters)
        else:
            semesters_json = "[]"

        risk_flags = opp.get("fraud_risk_flags", [])
        risk_flags_json = json.dumps(risk_flags) if isinstance(risk_flags, list) else "[]"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO opportunities (
                id, name, sponsor, sponsor_type, category, university_types,
                eligible_institutions, degree_levels, fields_of_study, academic_years,
                domicile_requirements, district_requirements, other_geographic,
                kp_eligibility, charsadda_eligibility, merit_criteria, need_criteria,
                min_gpa_or_marks, income_cap, age_limit, gender, other_conditions,
                award_amount, benefits, duration, number_of_awards, application_procedure,
                required_documents, attestation_requirements, apply_url, opening_date,
                deadline, document_upload_deadline, expiry_date, cycle, contact_email,
                contact_phone, contact_address, source_url, evidence_quote,
                confirmed_by_official_source, charsadda_flag, kp_flag, pakistan_wide_kp_eligible,
                target_uni_flag, merged_districts_only, status, days_left, source_trust_tier,
                verification_badge, claimed_by_source, link_status_apply, link_status_source,
                first_seen, last_verified, is_reconfirmed_today, all_source_urls, notes,
                is_national, is_international, work_mode, paid_status, stipend_amount,
                eligible_semesters, is_fully_funded, is_partially_funded, is_need_based,
                is_merit_based, fraud_risk_score, fraud_risk_flags, raw_json
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?
            )
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                sponsor=excluded.sponsor,
                sponsor_type=excluded.sponsor_type,
                category=excluded.category,
                university_types=excluded.university_types,
                eligible_institutions=excluded.eligible_institutions,
                degree_levels=excluded.degree_levels,
                fields_of_study=excluded.fields_of_study,
                academic_years=excluded.academic_years,
                domicile_requirements=excluded.domicile_requirements,
                district_requirements=excluded.district_requirements,
                other_geographic=excluded.other_geographic,
                kp_eligibility=excluded.kp_eligibility,
                charsadda_eligibility=excluded.charsadda_eligibility,
                merit_criteria=excluded.merit_criteria,
                need_criteria=excluded.need_criteria,
                min_gpa_or_marks=excluded.min_gpa_or_marks,
                income_cap=excluded.income_cap,
                age_limit=excluded.age_limit,
                gender=excluded.gender,
                other_conditions=excluded.other_conditions,
                award_amount=excluded.award_amount,
                benefits=excluded.benefits,
                duration=excluded.duration,
                number_of_awards=excluded.number_of_awards,
                application_procedure=excluded.application_procedure,
                required_documents=excluded.required_documents,
                attestation_requirements=excluded.attestation_requirements,
                apply_url=excluded.apply_url,
                opening_date=excluded.opening_date,
                deadline=excluded.deadline,
                document_upload_deadline=excluded.document_upload_deadline,
                expiry_date=excluded.expiry_date,
                cycle=excluded.cycle,
                contact_email=excluded.contact_email,
                contact_phone=excluded.contact_phone,
                contact_address=excluded.contact_address,
                source_url=excluded.source_url,
                evidence_quote=excluded.evidence_quote,
                confirmed_by_official_source=excluded.confirmed_by_official_source,
                charsadda_flag=excluded.charsadda_flag,
                kp_flag=excluded.kp_flag,
                pakistan_wide_kp_eligible=excluded.pakistan_wide_kp_eligible,
                target_uni_flag=excluded.target_uni_flag,
                merged_districts_only=excluded.merged_districts_only,
                status=excluded.status,
                days_left=excluded.days_left,
                source_trust_tier=excluded.source_trust_tier,
                verification_badge=excluded.verification_badge,
                claimed_by_source=excluded.claimed_by_source,
                link_status_apply=excluded.link_status_apply,
                link_status_source=excluded.link_status_source,
                last_verified=excluded.last_verified,
                is_reconfirmed_today=excluded.is_reconfirmed_today,
                all_source_urls=excluded.all_source_urls,
                notes=excluded.notes,
                is_national=excluded.is_national,
                is_international=excluded.is_international,
                work_mode=excluded.work_mode,
                paid_status=excluded.paid_status,
                stipend_amount=excluded.stipend_amount,
                eligible_semesters=excluded.eligible_semesters,
                is_fully_funded=excluded.is_fully_funded,
                is_partially_funded=excluded.is_partially_funded,
                is_need_based=excluded.is_need_based,
                is_merit_based=excluded.is_merit_based,
                fraud_risk_score=excluded.fraud_risk_score,
                fraud_risk_flags=excluded.fraud_risk_flags,
                raw_json=excluded.raw_json;
            """, (
                opp_id,
                opp.get("name", "not stated"),
                opp.get("sponsor", "not stated"),
                opp.get("sponsor_type", "other"),
                category,
                opp.get("university_types", "not stated"),
                opp.get("eligible_institutions", "not stated"),
                opp.get("degree_levels", "not stated"),
                opp.get("fields_of_study", "not stated"),
                opp.get("academic_years", "not stated"),
                opp.get("domicile_requirements", "not stated"),
                opp.get("district_requirements", "not stated"),
                opp.get("other_geographic", "not stated"),
                opp.get("kp_eligibility", "not stated"),
                opp.get("charsadda_eligibility", "not stated"),
                opp.get("merit_criteria", "not stated"),
                opp.get("need_criteria", "not stated"),
                opp.get("min_gpa_or_marks", "not stated"),
                opp.get("income_cap", "not stated"),
                opp.get("age_limit", "not stated"),
                opp.get("gender", "not stated"),
                opp.get("other_conditions", "not stated"),
                opp.get("award_amount", "not stated"),
                opp.get("benefits", "not stated"),
                opp.get("duration", "not stated"),
                opp.get("number_of_awards", "not stated"),
                opp.get("application_procedure", "not stated"),
                opp.get("required_documents", "not stated"),
                opp.get("attestation_requirements", "not stated"),
                opp.get("apply_url", "not stated"),
                opp.get("opening_date", "not stated"),
                opp.get("deadline", "not stated"),
                opp.get("document_upload_deadline", "not stated"),
                opp.get("expiry_date", "not stated"),
                opp.get("cycle", "not stated"),
                opp.get("contact_email", "not stated"),
                opp.get("contact_phone", "not stated"),
                opp.get("contact_address", "not stated"),
                opp.get("source_url", "not stated"),
                opp.get("evidence_quote", "not stated"),
                1 if opp.get("confirmed_by_official_source") else 0,
                1 if opp.get("charsadda_flag") else 0,
                1 if opp.get("kp_flag") else 0,
                1 if opp.get("pakistan_wide_kp_eligible") else 0,
                1 if opp.get("target_uni_flag") else 0,
                1 if opp.get("merged_districts_only") else 0,
                opp.get("status", "Deadline not stated"),
                opp.get("days_left"),
                opp.get("source_trust_tier", 1),
                opp.get("verification_badge", "Unverified"),
                opp.get("claimed_by_source"),
                opp.get("link_status_apply", "not stated"),
                opp.get("link_status_source", "not stated"),
                opp.get("first_seen", date.today().strftime("%Y-%m-%d")),
                opp.get("last_verified", date.today().strftime("%Y-%m-%d")),
                1 if opp.get("is_reconfirmed_today", True) else 0,
                all_urls_json,
                opp.get("notes"),
                1 if opp.get("is_national", True) else 0,
                1 if opp.get("is_international", False) else 0,
                opp.get("work_mode", "not stated"),
                opp.get("paid_status", "not stated"),
                opp.get("stipend_amount", "not stated"),
                semesters_json,
                1 if opp.get("is_fully_funded", False) else 0,
                1 if opp.get("is_partially_funded", False) else 0,
                1 if opp.get("is_need_based", False) else 0,
                1 if opp.get("is_merit_based", False) else 0,
                float(opp.get("fraud_risk_score", 0.0)),
                risk_flags_json,
                json.dumps(opp)
            ))
            conn.commit()
        return opp_id

    def record_change(self, opp_id: str, change_type: str, field_name: str, old_val: str, new_val: str, detected_at: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO opportunity_changes (opportunity_id, change_type, field_name, old_value, new_value, detected_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (opp_id, change_type, field_name, old_val, new_val, detected_at))
            conn.commit()

    def get_opportunity(self, opp_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None

    def get_all_opportunities(self, category: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        query = "SELECT * FROM opportunities WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if active_only:
            query += " AND status NOT IN ('Closed', 'Previous cycle – awaiting new call')"
        query += " ORDER BY CASE WHEN days_left IS NULL THEN 9999 ELSE days_left END ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # Parse JSON fields
        for jf in ["all_source_urls", "eligible_semesters", "fraud_risk_flags"]:
            if jf in d and d[jf]:
                try:
                    d[jf] = json.loads(d[jf])
                except Exception:
                    d[jf] = []
        # Convert integers to bool
        for bf in ["confirmed_by_official_source", "charsadda_flag", "kp_flag",
                   "pakistan_wide_kp_eligible", "target_uni_flag", "merged_districts_only",
                   "is_reconfirmed_today", "is_national", "is_international",
                   "is_fully_funded", "is_partially_funded", "is_need_based", "is_merit_based"]:
            if bf in d:
                d[bf] = bool(d[bf])
        return d

    # ---------------- Student Profile CRUD ----------------
    def save_student(self, student: Any) -> str:
        if hasattr(student, "model_dump"):
            student = student.model_dump()
        elif hasattr(student, "dict"):
            student = student.dict()
        s_id = student.get("id")
        email = student.get("email", "")
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            if not s_id and email:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
                row = cursor.fetchone()
                if row:
                    s_id = row["id"]
            if not s_id:
                s_id = f"STU-{uuid.uuid4().hex[:10]}"

            conn.execute("""
            INSERT INTO students (
                id, full_name, email, phone, university, university_type,
                degree_level, discipline, current_semester, cgpa,
                domicile_district, domicile_province, work_preference,
                funding_need, skills, interests, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                full_name=excluded.full_name,
                email=excluded.email,
                phone=excluded.phone,
                university=excluded.university,
                university_type=excluded.university_type,
                degree_level=excluded.degree_level,
                discipline=excluded.discipline,
                current_semester=excluded.current_semester,
                cgpa=excluded.cgpa,
                domicile_district=excluded.domicile_district,
                domicile_province=excluded.domicile_province,
                work_preference=excluded.work_preference,
                funding_need=excluded.funding_need,
                skills=excluded.skills,
                interests=excluded.interests,
                updated_at=excluded.updated_at;
            """, (
                s_id,
                student.get("full_name", "Student"),
                student.get("email", ""),
                student.get("phone", ""),
                student.get("university", "University of Peshawar"),
                student.get("university_type", "public"),
                student.get("degree_level", "Undergraduate"),
                student.get("discipline", "Computer Science"),
                int(student.get("current_semester", 1)),
                float(student.get("cgpa", 3.0)),
                student.get("domicile_district", "Charsadda"),
                student.get("domicile_province", "Khyber Pakhtunkhwa"),
                student.get("work_preference", "any"),
                student.get("funding_need", "any"),
                json.dumps(student.get("skills", [])),
                json.dumps(student.get("interests", [])),
                student.get("created_at", now_str),
                now_str
            ))
            conn.commit()
        return s_id

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ? OR email = ?", (student_id, student_id))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["skills"] = json.loads(d["skills"]) if d.get("skills") else []
                d["interests"] = json.loads(d["interests"]) if d.get("interests") else []
                return d
        return None

    def list_students(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students ORDER BY full_name ASC")
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["skills"] = json.loads(d["skills"]) if d.get("skills") else []
                d["interests"] = json.loads(d["interests"]) if d.get("interests") else []
                results.append(d)
            return results

    # ---------------- Student Matches CRUD ----------------
    def save_match(self, match: Dict[str, Any]) -> None:
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO student_matches (
                student_id, opportunity_id, match_score, eligibility_status,
                reasons, unmet_criteria, unknown_criteria, recommended_priority, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, opportunity_id) DO UPDATE SET
                match_score=excluded.match_score,
                eligibility_status=excluded.eligibility_status,
                reasons=excluded.reasons,
                unmet_criteria=excluded.unmet_criteria,
                unknown_criteria=excluded.unknown_criteria,
                recommended_priority=excluded.recommended_priority,
                updated_at=excluded.updated_at;
            """, (
                match["student_id"],
                match["opportunity_id"],
                float(match.get("match_score", 0.0)),
                match.get("eligibility_status", "likely_eligible"),
                json.dumps(match.get("reasons", [])),
                json.dumps(match.get("unmet_criteria", [])),
                json.dumps(match.get("unknown_criteria", [])),
                match.get("recommended_priority", "medium"),
                now_str
            ))
            conn.commit()

    def get_student_matches(self, student_id: str, min_score: float = 0.0) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT m.*, o.name as opp_name, o.sponsor, o.deadline, o.status as opp_status,
                   o.category as opp_category, o.award_amount, o.apply_url, o.charsadda_flag, o.kp_flag
            FROM student_matches m
            JOIN opportunities o ON m.opportunity_id = o.id
            WHERE m.student_id = ? AND m.match_score >= ?
            ORDER BY m.match_score DESC
            """, (student_id, min_score))
            matches = []
            for r in cursor.fetchall():
                d = dict(r)
                d["reasons"] = json.loads(d["reasons"]) if d.get("reasons") else []
                d["unmet_criteria"] = json.loads(d["unmet_criteria"]) if d.get("unmet_criteria") else []
                d["unknown_criteria"] = json.loads(d["unknown_criteria"]) if d.get("unknown_criteria") else []
                matches.append(d)
            return matches

    # ---------------- Application Tracking CRUD ----------------
    def save_application(self, app_data: Any) -> str:
        data = app_data.model_dump() if hasattr(app_data, "model_dump") else dict(app_data)
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM applications WHERE student_id = ? AND opportunity_id = ?", (data["student_id"], data["opportunity_id"]))
            existing_row = cursor.fetchone()
            if existing_row:
                app_id = existing_row["id"]
            else:
                app_id = data.get("id") or f"APP_{uuid.uuid4().hex[:10]}"

            conn.execute("""
            INSERT INTO applications (
                id, student_id, opportunity_id, status, deadline, notes,
                tasks_json, documents_checklist_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, opportunity_id) DO UPDATE SET
                status=excluded.status,
                deadline=excluded.deadline,
                notes=excluded.notes,
                tasks_json=excluded.tasks_json,
                documents_checklist_json=excluded.documents_checklist_json,
                updated_at=excluded.updated_at;
            """, (
                app_id,
                data["student_id"],
                data["opportunity_id"],
                data.get("status", "interested"),
                data.get("deadline", ""),
                data.get("notes", ""),
                json.dumps(data.get("tasks", [])),
                json.dumps(data.get("documents_checklist", [])),
                data.get("created_at", now_str),
                now_str
            ))
            conn.commit()
        return app_id

    def list_applications(self, student_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT a.*, o.name as opp_name, o.sponsor, o.deadline as opp_deadline, o.apply_url, o.category
            FROM applications a
            JOIN opportunities o ON a.opportunity_id = o.id
            WHERE a.student_id = ?
            ORDER BY a.updated_at DESC
            """, (student_id,))
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["tasks"] = json.loads(d["tasks_json"]) if d.get("tasks_json") else []
                d["documents_checklist"] = json.loads(d["documents_checklist_json"]) if d.get("documents_checklist_json") else []
                results.append(d)
            return results

    # ---------------- Agent Jobs & Telemetry ----------------
    def record_job(self, job_data: Dict[str, Any]) -> str:
        job_id = job_data.get("id") or f"JOB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO agent_jobs (
                id, agent_name, run_type, status, started_at, completed_at,
                items_discovered, items_extracted, items_verified, errors_json,
                tokens_used, cost_estimate_usd, log_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                completed_at=excluded.completed_at,
                items_discovered=excluded.items_discovered,
                items_extracted=excluded.items_extracted,
                items_verified=excluded.items_verified,
                errors_json=excluded.errors_json,
                tokens_used=excluded.tokens_used,
                cost_estimate_usd=excluded.cost_estimate_usd,
                log_summary=excluded.log_summary;
            """, (
                job_id,
                job_data.get("agent_name", "MasterOrchestrator"),
                job_data.get("run_type", "manual"),
                job_data.get("status", "completed"),
                job_data.get("started_at", datetime.now().isoformat()),
                job_data.get("completed_at", datetime.now().isoformat()),
                int(job_data.get("items_discovered", 0)),
                int(job_data.get("items_extracted", 0)),
                int(job_data.get("items_verified", 0)),
                json.dumps(job_data.get("errors", [])),
                int(job_data.get("tokens_used", 0)),
                float(job_data.get("cost_estimate_usd", 0.0)),
                job_data.get("log_summary", "")
            ))
            conn.commit()
        return job_id

    def list_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_jobs ORDER BY started_at DESC LIMIT ?", (limit,))
            jobs = []
            for r in cursor.fetchall():
                d = dict(r)
                d["errors"] = json.loads(d["errors_json"]) if d.get("errors_json") else []
                jobs.append(d)
            return jobs

    # ---------------- Report History ----------------
    def record_report(self, report_data: Dict[str, Any]) -> str:
        rep_id = report_data.get("id") or f"REP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{report_data.get('report_number', '00')}"
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO reports_history (
                id, report_number, report_title, category, generated_at,
                total_records, file_paths_json, filters_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rep_id,
                str(report_data.get("report_number", "")),
                report_data.get("report_title", ""),
                report_data.get("category", "General"),
                report_data.get("generated_at", datetime.now().isoformat()),
                int(report_data.get("total_records", 0)),
                json.dumps(report_data.get("file_paths", {})),
                json.dumps(report_data.get("filters", {}))
            ))
            conn.commit()
        return rep_id

    def list_reports_history(self, limit: int = 40) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports_history ORDER BY generated_at DESC LIMIT ?", (limit,))
            reps = []
            for r in cursor.fetchall():
                d = dict(r)
                d["file_paths"] = json.loads(d["file_paths_json"]) if d.get("file_paths_json") else {}
                d["filters"] = json.loads(d["filters_json"]) if d.get("filters_json") else {}
                reps.append(d)
            return reps

    # ---------------- Adapter Methods for Typed Models ----------------
    def list_opportunities(self, category: Optional[str] = None, active_only: bool = False):
        from agent.models import OpportunityRecord
        raw_list = self.get_all_opportunities(category=category, active_only=active_only)
        records = []
        for r in raw_list:
            try:
                # Remove raw_json if it conflicts
                clean_dict = {k: v for k, v in r.items() if k != "raw_json"}
                records.append(OpportunityRecord(**clean_dict))
            except Exception as e:
                logger.warning(f"Failed to cast opportunity {r.get('id')} to OpportunityRecord: {e}")
        return records

    def record_agent_job(self, job_id: str, agent_name: str, status: str, details: str = "", **kwargs) -> str:
        return self.record_job({
            "id": job_id,
            "agent_name": agent_name,
            "status": status,
            "log_summary": details,
            **kwargs
        })

    def record_report_generation(
        self,
        report_id: str,
        report_number: str,
        title: str,
        format_type: str,
        file_path: str,
        record_count: int,
        filters_applied: str = ""
    ) -> str:
        return self.record_report({
            "id": report_id,
            "report_number": report_number,
            "report_title": title,
            "category": f"Report-{report_number}",
            "total_records": record_count,
            "file_paths": {format_type: file_path},
            "filters": {"applied": filters_applied}
        })

    def log_audit(self, actor: str, action: str, details: str = "", target_type: str = "SYSTEM", target_id: str = "") -> None:
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO audit_logs (actor, action, target_type, target_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (actor, action, target_type, target_id, details, datetime.now().isoformat()))
            conn.commit()

    def list_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunity_changes ORDER BY detected_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def list_sources(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources ORDER BY tier ASC, name ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_application(self, app_id: str):
        from agent.models import ApplicationRecord
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["tasks"] = json.loads(d["tasks_json"]) if d.get("tasks_json") else []
                d["documents_checklist"] = json.loads(d["documents_checklist_json"]) if d.get("documents_checklist_json") else []
                return ApplicationRecord(
                    id=d["id"],
                    student_id=d["student_id"],
                    opportunity_id=d["opportunity_id"],
                    status=d.get("status", "interested"),
                    deadline=d.get("deadline", "") or "",
                    notes=d.get("notes", "") or "",
                    tasks=d.get("tasks", []),
                    documents_checklist=d.get("documents_checklist", []),
                    created_at=d.get("created_at", ""),
                    updated_at=d.get("updated_at", "")
                )
        return None

    def list_applications_for_student(self, student_id: str):
        from agent.models import ApplicationRecord
        raw_apps = self.list_applications(student_id)
        records = []
        for d in raw_apps:
            records.append(ApplicationRecord(
                id=d["id"],
                student_id=d["student_id"],
                opportunity_id=d["opportunity_id"],
                opportunity_name=d.get("opp_name", ""),
                sponsor=d.get("sponsor", ""),
                status=d.get("status", "interested"),
                deadline=d.get("deadline", "") or "",
                notes=d.get("notes", "") or "",
                tasks=d.get("tasks", []),
                documents_checklist=d.get("documents_checklist", []),
                created_at=d.get("created_at", ""),
                updated_at=d.get("updated_at", "")
            ))
        return records

    def save_student_matches(self, student_id: str, matches) -> None:
        for m in matches:
            if hasattr(m, "model_dump"):
                self.save_match(m.model_dump())
            elif isinstance(m, dict):
                self.save_match(m)

    def list_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def list_notifications(self, student_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if student_id:
                cursor.execute("""
                SELECT * FROM notifications 
                WHERE student_id = ? OR student_id IS NULL OR student_id = ''
                ORDER BY sent_at DESC LIMIT ?
                """, (student_id, limit))
            else:
                cursor.execute("SELECT * FROM notifications ORDER BY sent_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def mark_notification_read(self, notification_id: int) -> bool:
        with self.get_connection() as conn:
            now_iso = datetime.now().isoformat()
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET read_at = ? WHERE id = ?", (now_iso, notification_id))
            conn.commit()
            return cursor.rowcount > 0

    def mark_all_notifications_read(self, student_id: Optional[str] = None) -> int:
        with self.get_connection() as conn:
            now_iso = datetime.now().isoformat()
            cursor = conn.cursor()
            if student_id:
                cursor.execute("""
                UPDATE notifications SET read_at = ? 
                WHERE read_at IS NULL AND (student_id = ? OR student_id IS NULL OR student_id = '')
                """, (now_iso, student_id))
            else:
                cursor.execute("UPDATE notifications SET read_at = ? WHERE read_at IS NULL", (now_iso,))
            conn.commit()
            return cursor.rowcount

    def save_source(self, source_dict: Dict[str, Any]) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO sources (
                url, name, tier, category, status, last_checked, last_success, 
                consecutive_failures, items_discovered, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_dict.get("url", ""),
                source_dict.get("name", "Unknown Source"),
                int(source_dict.get("tier", 1)),
                source_dict.get("category", "general"),
                source_dict.get("status", "active"),
                source_dict.get("last_checked", datetime.now().isoformat()),
                source_dict.get("last_success", datetime.now().isoformat()),
                int(source_dict.get("consecutive_failures", 0)),
                int(source_dict.get("items_discovered", 0)),
                source_dict.get("error_message", "")
            ))
            conn.commit()
            return source_dict.get("url", "")

    def update_opportunity(self, opp_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            allowed_fields = [
                "name", "sponsor", "category", "university_types", "status", "deadline",
                "days_left", "verification_badge", "confirmed_by_official_source",
                "source_trust_tier", "notes", "award_amount", "benefits", "apply_url",
                "fraud_risk_score", "fraud_risk_flags"
            ]
            set_clauses = []
            values = []
            for k, v in updates.items():
                if k in allowed_fields:
                    set_clauses.append(f"{k} = ?")
                    if isinstance(v, (list, dict)):
                        values.append(json.dumps(v))
                    else:
                        values.append(v)
            if not set_clauses:
                return self.get_opportunity(opp_id)
            set_clauses.append("last_verified = ?")
            values.append(datetime.now().isoformat())
            values.append(opp_id)
            sql = f"UPDATE opportunities SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()
            self.log_audit("ADMIN", "UPDATE_OPPORTUNITY", f"Updated fields: {list(updates.keys())}", "OPPORTUNITY", opp_id)
            return self.get_opportunity(opp_id)

    def get_verification_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM opportunities 
            WHERE verification_badge = 'Unverified' 
               OR confirmed_by_official_source = 0 
               OR fraud_risk_score > 0.0
               OR link_status_apply LIKE '4%' 
               OR link_status_apply LIKE '5%'
            ORDER BY fraud_risk_score DESC, deadline ASC 
            LIMIT ?
            """, (limit,))
            return [self._row_to_dict(r) for r in cursor.fetchall()]

    def list_saved_opportunities(self, student_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT o.*, s.saved_at 
            FROM opportunities o 
            JOIN saved_opportunities s ON o.id = s.opportunity_id 
            WHERE s.student_id = ? 
            ORDER BY s.saved_at DESC
            """, (student_id,))
            return [self._row_to_dict(r) for r in cursor.fetchall()]

    def toggle_saved_opportunity(self, student_id: str, opportunity_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM saved_opportunities WHERE student_id = ? AND opportunity_id = ?", (student_id, opportunity_id))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("DELETE FROM saved_opportunities WHERE student_id = ? AND opportunity_id = ?", (student_id, opportunity_id))
                conn.commit()
                return False  # Unsaved
            else:
                now_iso = datetime.now().isoformat()
                cursor.execute("INSERT INTO saved_opportunities (student_id, opportunity_id, saved_at) VALUES (?, ?, ?)", (student_id, opportunity_id, now_iso))
                conn.commit()
                return True  # Saved

    def is_opportunity_saved(self, student_id: str, opportunity_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM saved_opportunities WHERE student_id = ? AND opportunity_id = ?", (student_id, opportunity_id))
            return cursor.fetchone() is not None

    def get_settings(self) -> Dict[str, Any]:
        default_settings = {
            "platform_name": "Student Opportunity Intelligence",
            "subtitle": "Discover. Qualify. Apply. Achieve.",
            "brand_color": "#0284C7",
            "theme": "light",
            "ai_model": os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            "schedule_time": os.environ.get("SCHEDULE_TIME", "07:00"),
            "owner_email": os.environ.get("OWNER_EMAIL", "admin@example.com"),
            "resend_from_email": os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
            "default_report_formats": ["pdf", "xlsx", "csv", "html"],
            "max_daily_budget_usd": 5.0,
            "rate_limit_rpm": 60,
            "charsadda_priority_weight": 1.2
        }
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value_json FROM system_settings")
            rows = cursor.fetchall()
            for r in rows:
                try:
                    default_settings[r["key"]] = json.loads(r["value_json"])
                except Exception:
                    default_settings[r["key"]] = r["value_json"]
        return default_settings

    def save_settings(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            for k, v in settings_dict.items():
                val_str = json.dumps(v) if isinstance(v, (dict, list, bool, int, float)) else str(v)
                cursor.execute("INSERT OR REPLACE INTO system_settings (key, value_json, updated_at) VALUES (?, ?, ?)", (k, val_str, now_iso))
            conn.commit()
            self.log_audit("ADMIN", "UPDATE_SETTINGS", f"Updated {len(settings_dict)} settings", "SYSTEM", "CONFIG")
        return self.get_settings()

    def get_admin_metrics(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Opportunities breakdown
            cursor.execute("SELECT COUNT(*) FROM opportunities")
            total_opps = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE status = 'Open'")
            open_opps = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE status = 'Closing soon'")
            closing_soon = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE category = 'scholarships'")
            scholarships_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE category = 'internships'")
            internships_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE verification_badge = 'Unverified' OR confirmed_by_official_source = 0")
            unverified_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE days_left >= 0 AND days_left <= 30")
            upcoming_deadlines = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reports_history")
            total_reports = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM sources WHERE consecutive_failures > 0 OR status != 'active'")
            sources_attention = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM sources")
            total_sources = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM applications")
            total_applications = cursor.fetchone()[0]

            # Category distribution
            cursor.execute("SELECT category, COUNT(*) as cnt FROM opportunities GROUP BY category ORDER BY cnt DESC")
            cat_dist = {r["category"]: r["cnt"] for r in cursor.fetchall()}

            # University types distribution
            cursor.execute("SELECT university_types, COUNT(*) as cnt FROM opportunities GROUP BY university_types")
            uni_dist = {r["university_types"]: r["cnt"] for r in cursor.fetchall()}

            # Status distribution
            cursor.execute("SELECT status, COUNT(*) as cnt FROM opportunities GROUP BY status")
            status_dist = {r["status"]: r["cnt"] for r in cursor.fetchall()}

            # National vs International
            cursor.execute("SELECT SUM(is_national) as nat, SUM(is_international) as intl FROM opportunities")
            nat_row = cursor.fetchone()
            scope_dist = {
                "national": nat_row["nat"] or 0,
                "international": nat_row["intl"] or 0
            }

            return {
                "total_opportunities": total_opps,
                "open_opportunities": open_opps,
                "closing_soon": closing_soon,
                "scholarships_count": scholarships_count,
                "internships_count": internships_count,
                "unverified_count": unverified_count,
                "upcoming_deadlines": upcoming_deadlines,
                "total_students": total_students,
                "total_reports": total_reports,
                "total_sources": total_sources,
                "sources_attention": sources_attention,
                "total_applications": total_applications,
                "category_distribution": cat_dist,
                "university_type_distribution": uni_dist,
                "status_distribution": status_dist,
                "scope_distribution": scope_dist
            }

    def global_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        q = f"%{query.strip().lower()}%"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Search opportunities
            cursor.execute("""
            SELECT id, name, sponsor, category, status, deadline, verification_badge 
            FROM opportunities 
            WHERE lower(name) LIKE ? OR lower(sponsor) LIKE ? OR lower(benefits) LIKE ? OR lower(fields_of_study) LIKE ?
            LIMIT ?
            """, (q, q, q, q, limit))
            opp_results = [dict(r) for r in cursor.fetchall()]

            # Search sources
            cursor.execute("""
            SELECT url, name, category, status, tier 
            FROM sources 
            WHERE lower(name) LIKE ? OR lower(url) LIKE ?
            LIMIT 5
            """, (q, q))
            source_results = [dict(r) for r in cursor.fetchall()]

            # Search students
            cursor.execute("""
            SELECT id, full_name, email, university, discipline 
            FROM students 
            WHERE lower(full_name) LIKE ? OR lower(email) LIKE ? OR lower(university) LIKE ?
            LIMIT 5
            """, (q, q, q))
            student_results = [dict(r) for r in cursor.fetchall()]

            return {
                "query": query,
                "opportunities": opp_results,
                "sources": source_results,
                "students": student_results
            }

    # ---------------- Authentication & User Management ----------------
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, salt: str, password_hash: str) -> bool:
        test_hash, _ = Database.hash_password(password, salt)
        return secrets.compare_digest(test_hash, password_hash)

    def seed_default_users(self) -> None:
        """Seeds default admin and student accounts if none exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_str = datetime.now(timezone.utc).isoformat()

            # Ensure Default Admin exists
            cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@opportunity.edu.pk",))
            if not cursor.fetchone():
                admin_hash, admin_salt = self.hash_password("AdminPassword123!")
                cursor.execute("""
                INSERT INTO users (id, email, password_hash, salt, role, full_name, is_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """, (str(uuid.uuid4()), "admin@opportunity.edu.pk", admin_hash, admin_salt, "admin", "Platform Administrator", now_str))

            # Ensure Default Student exists
            cursor.execute("SELECT id FROM users WHERE email = ?", ("student@uop.edu.pk",))
            if not cursor.fetchone():
                cursor.execute("SELECT id, full_name FROM students WHERE email = ? LIMIT 1", ("student@uop.edu.pk",))
                row = cursor.fetchone()
                stu_id = row["id"] if row else None
                stu_name = row["full_name"] if row else "Ahmad Khan"

                stu_hash, stu_salt = self.hash_password("StudentPassword123!")
                cursor.execute("""
                INSERT INTO users (id, email, password_hash, salt, role, full_name, is_verified, student_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """, (str(uuid.uuid4()), "student@uop.edu.pk", stu_hash, stu_salt, "student", stu_name, stu_id, now_str))

            conn.commit()

    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "student",
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registers a new user with secure password hash and verification token."""
        clean_email = email.strip().lower()
        now_str = datetime.now(timezone.utc).isoformat()
        pwd_hash, salt = self.hash_password(password)
        v_token = secrets.token_urlsafe(32)
        uid = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
            if cursor.fetchone():
                raise ValueError(f"An account with email {clean_email} already exists.")

            # If student, link or create student profile
            linked_student_id = student_id
            if role == "student" and not linked_student_id:
                cursor.execute("SELECT id FROM students WHERE email = ?", (clean_email,))
                existing_stu = cursor.fetchone()
                if existing_stu:
                    linked_student_id = existing_stu["id"]
                else:
                    new_stu_id = f"STU-{abs(hash(clean_email)) % 1000000000}"
                    cursor.execute("""
                    INSERT INTO students (id, full_name, email, university, discipline, current_semester, cgpa, domicile_district, domicile_province, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_stu_id, full_name, clean_email, "University of Peshawar", "Computer Science", 1, 3.0, "Charsadda", "Khyber Pakhtunkhwa", now_str, now_str))
                    linked_student_id = new_stu_id

            cursor.execute("""
            INSERT INTO users (id, email, password_hash, salt, role, full_name, is_verified, verification_token, student_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """, (uid, clean_email, pwd_hash, salt, role, full_name, v_token, linked_student_id, now_str))
            conn.commit()

        return {
            "id": uid,
            "email": clean_email,
            "full_name": full_name,
            "role": role,
            "student_id": linked_student_id,
            "is_verified": False,
            "verification_token": v_token
        }

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials and returns user payload if valid."""
        clean_email = email.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, email, password_hash, salt, role, full_name, is_verified, student_id, created_at
            FROM users WHERE email = ?
            """, (clean_email,))
            user = cursor.fetchone()
            if not user:
                return None

            if not self.verify_password(password, user["salt"], user["password_hash"]):
                return None

            now_str = datetime.now(timezone.utc).isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user["id"]))
            conn.commit()

            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "is_verified": bool(user["is_verified"]),
                "student_id": user["student_id"],
                "created_at": user["created_at"],
                "last_login": now_str
            }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, email, role, full_name, is_verified, student_id, created_at, last_login
            FROM users WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, email, role, full_name, is_verified, student_id, created_at, last_login
            FROM users WHERE email = ?
            """, (email.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_session(self, user_id: str, email: str, role: str, student_id: Optional[str] = None, expires_days: int = 7) -> str:
        token = secrets.token_urlsafe(48)
        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        expires_at = (now + timedelta(days=expires_days)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (token, user_id, email, role, student_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (token, user_id, email, role, student_id, created_at, expires_at))
            conn.commit()
        return token

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT token, user_id, email, role, student_id, created_at, expires_at
            FROM sessions WHERE token = ?
            """, (token,))
            row = cursor.fetchone()
            if not row:
                return None
            sess = dict(row)
            expires = datetime.fromisoformat(sess["expires_at"])
            if expires < datetime.now(timezone.utc):
                cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                return None
            return sess

    def delete_session(self, token: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0

    def verify_email_token(self, token: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE verification_token = ?", (token,))
            user = cursor.fetchone()
            if not user:
                return False
            cursor.execute("UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?", (user["id"],))
            conn.commit()
            return True

    def create_password_reset_token(self, email: str) -> Optional[str]:
        clean_email = email.strip().lower()
        reset_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
            if not cursor.fetchone():
                return None
            cursor.execute("""
            UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE email = ?
            """, (reset_token, expires_at, clean_email))
            conn.commit()
            return reset_token

    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, reset_token_expires FROM users WHERE reset_token = ?
            """, (token,))
            user = cursor.fetchone()
            if not user:
                return False
            if user["reset_token_expires"]:
                exp = datetime.fromisoformat(user["reset_token_expires"])
                if exp < datetime.now(timezone.utc):
                    return False
            pwd_hash, salt = self.hash_password(new_password)
            cursor.execute("""
            UPDATE users SET password_hash = ?, salt = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?
            """, (pwd_hash, salt, user["id"]))
            # Security Hardening: Invalidate all existing sessions upon password reset
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
            conn.commit()
            return True

    def delete_user_account(self, user_id: str, password: str) -> bool:
        """Securely deletes a user account, sessions, and linked student data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, salt, password_hash, role, student_id FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False
            if not self.verify_password(password, user["salt"], user["password_hash"]):
                return False
            
            # If student, delete associated applications, matches, saved opportunities
            if user["student_id"]:
                sid = user["student_id"]
                cursor.execute("DELETE FROM applications WHERE student_id = ?", (sid,))
                cursor.execute("DELETE FROM student_matches WHERE student_id = ?", (sid,))
                cursor.execute("DELETE FROM saved_opportunities WHERE student_id = ?", (sid,))
                cursor.execute("DELETE FROM students WHERE id = ?", (sid,))

            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True

    # ---------------- Analytics & Telemetry Tracking ----------------
    def log_analytics_event(
        self,
        event_name: str,
        category: str,
        properties: Optional[Dict[str, Any]] = None,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        now_str = datetime.now(timezone.utc).isoformat()
        props_str = json.dumps(properties or {})
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO analytics_events (event_name, category, properties_json, anonymous_id, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (event_name, category, props_str, anonymous_id, user_id, now_str))
            conn.commit()
            return cursor.lastrowid

    def get_analytics_summary(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analytics_events")
            total_events = cursor.fetchone()[0]
            cursor.execute("""
            SELECT event_name, COUNT(*) as count 
            FROM analytics_events 
            GROUP BY event_name 
            ORDER BY count DESC 
            LIMIT 10
            """)
            top_events = [dict(r) for r in cursor.fetchall()]
            return {
                "total_events": total_events,
                "top_events": top_events
            }

    # ---------------- Error Tracking ----------------
    def log_frontend_error(
        self,
        error_message: str,
        stack_trace: str = "",
        url: str = "",
        user_agent: str = "",
        user_id: Optional[str] = None
    ) -> int:
        now_str = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO frontend_errors (error_message, stack_trace, url, user_agent, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (error_message[:1000], stack_trace[:4000], url[:500], user_agent[:300], user_id, now_str))
            conn.commit()
            return cursor.lastrowid

    def list_frontend_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, error_message, stack_trace, url, user_agent, user_id, created_at
            FROM frontend_errors
            ORDER BY id DESC
            LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ---------------- Automated Database Backups ----------------
    def create_backup(self) -> Dict[str, Any]:
        """Creates an atomic, timestamped SQLite backup in data/backups/."""
        backups_dir = self.db_path.parent / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"opportunities_backup_{now_str}.db"
        target_path = backups_dir / backup_filename

        with self.get_connection() as conn:
            dest_conn = sqlite3.connect(str(target_path))
            conn.backup(dest_conn)
            dest_conn.close()

        size_bytes = target_path.stat().st_size
        return {
            "filename": backup_filename,
            "path": str(target_path),
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        backups_dir = self.db_path.parent / "backups"
        if not backups_dir.exists():
            return []
        items = []
        for p in backups_dir.glob("opportunities_backup_*.db"):
            items.append({
                "filename": p.name,
                "size_kb": round(p.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
            })
        items.sort(key=lambda x: x["filename"], reverse=True)
        return items

    def restore_backup(self, backup_filename: str) -> bool:
        if not backup_filename or not isinstance(backup_filename, str):
            raise ValueError("Backup filename required.")
        if ".." in backup_filename or "/" in backup_filename or "\\" in backup_filename or "%" in backup_filename:
            raise ValueError("Path traversal characters rejected in backup filename.")
        if not re.match(r"^opportunities_backup_[a-zA-Z0-9_\-]+\.db$", backup_filename):
            raise ValueError("Disallowed backup file format.")

        backups_dir = (self.db_path.parent / "backups").resolve()
        target_path = (backups_dir / backup_filename).resolve()
        if target_path.parent != backups_dir or not target_path.exists():
            raise FileNotFoundError("Backup file not found or path traversal rejected.")

        # Emergency pre-restore snapshot
        self.create_backup()

        src_conn = sqlite3.connect(str(target_path))
        with self.get_connection() as dest_conn:
            src_conn.backup(dest_conn)
        src_conn.close()
        return True


# Backward and alias compatibility
OpportunityDB = Database

