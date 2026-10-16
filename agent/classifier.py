"""Classifier module for university sectors (HEC recognized) and priority flags.
Enforces that IMSciences is classified as a public-sector institution according to HEC.
Calculates flags: charsadda_flag, kp_flag, pakistan_wide_kp_eligible, target_uni_flag, merged_districts_only.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from agent.models import ScholarshipRecord, UniversityTypes


EX_FATA_MERGED_DISTRICTS = {
    "bajaur", "mohmand", "khyber", "orakzai", "kurram",
    "north waziristan", "south waziristan", "fr peshawar", "fr kohat",
    "fr bannu", "fr lakki", "fr tank", "fr di khan", "ex-fata", "merged districts"
}

PUBLIC_TARGET_KEYWORDS = [
    "university of peshawar", "uop", "uet peshawar", "university of engineering and technology peshawar"
]

PRIVATE_TARGET_KEYWORDS = [
    "abasyn university", "abasyn peshawar"
]

KP_PUBLIC_PRIORITY_KEYWORDS = [
    "bacha khan university", "bkuc", "islamia college peshawar", "icp",
    "khyber medical university", "kmu", "university of agriculture peshawar", "aup",
    "abdul wali khan university", "awkum", "imsciences", "institute of management sciences peshawar"
]

KP_PRIVATE_PRIORITY_KEYWORDS = [
    "cecos", "iqra national", "city university", "cusit", "sarhad university", "suit"
]


class UniversityClassifier:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "config" / "universities.json"
        
        self.public_unis = []
        self.private_unis = []
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.public_unis = data.get("public_universities", [])
                self.private_unis = data.get("private_universities", [])

    def classify_university_name(self, text: str) -> UniversityTypes:
        """Determines if a named institution is public or private based on HEC records."""
        low = text.lower()

        # IMSciences explicit check: always public sector according to HEC
        if "imsciences" in low or "institute of management sciences" in low:
            return "public"

        words = set(re.findall(r"\b\w+\b", low))

        # Check explicit public target list
        for u in self.public_unis:
            u_name = u["name"].lower()
            abbr = u.get("abbreviation", "").lower()
            # Match full name, abbreviation as substring or token, or key identifier
            if u_name in low or (abbr and (abbr in low or abbr in words)):
                return "public"
            # Special check for UET Peshawar
            if "uet" in words and "peshawar" in low:
                return "public"

        # Check explicit private target list
        for u in self.private_unis:
            u_name = u["name"].lower()
            abbr = u.get("abbreviation", "").lower()
            if u_name in low or (abbr and (abbr in low or abbr in words)):
                return "private"
            # Special checks for common names: City University, CECOS, Abasyn, Iqra National, Sarhad
            if "city university" in low or "cecos" in low or "abasyn" in low or "iqra national" in low or "sarhad university" in low:
                return "private"

        # Common indicators
        if any(term in low for term in ["public university", "government university", "public sector"]):
            return "public"
        if any(term in low for term in ["private university", "private sector"]):
            return "private"

        return "not stated"

    def calculate_priority_flags(
        self, record_data: Dict[str, Any], report_type: str = "public"
    ) -> Tuple[bool, bool, bool, bool, bool]:
        """Calculates (charsadda_flag, kp_flag, pakistan_wide_kp_eligible, target_uni_flag, merged_districts_only).
        
        Section 5 rules:
        - charsadda_flag: Charsadda named explicitly, or scheme is for a district/zone that includes Charsadda,
          or it is reserved for Bacha Khan University Charsadda.
        - kp_flag: KP domicile explicitly required or favoured, or a KP-wide programme.
        - pakistan_wide_kp_eligible: open to all of Pakistan and KP is not excluded.
        - target_uni_flag: names UoP or UET Peshawar (public report), or Abasyn University (private report).
        - merged_districts_only: limited to the ex-FATA merged districts. Charsadda is NOT a merged district,
          so these records must not get the Charsadda flag.
        """
        combined_text = " ".join(
            str(record_data.get(k, "") or "")
            for k in [
                "name", "sponsor", "eligible_institutions", "domicile_requirements",
                "district_requirements", "other_geographic", "other_conditions",
                "benefits", "evidence_quote"
            ]
        ).lower()

        # 1. Merged districts check
        is_merged_only = False
        has_merged_mention = any(m in combined_text for m in EX_FATA_MERGED_DISTRICTS)
        if has_merged_mention and not any(k in combined_text for k in ["settled districts", "all kp", "all pakistan", "whole kp"]):
            # If specifically restricted to merged districts/FATA
            if any(term in combined_text for term in ["merged districts only", "ex-fata only", "tribal districts only", "for merged districts"]):
                is_merged_only = True

        # 2. Charsadda flag
        # Charsadda is NOT a merged district. Never set charsadda_flag if merged_districts_only is true.
        charsadda_flag = False
        if not is_merged_only:
            if "charsadda" in combined_text or "bacha khan university" in combined_text or "bkuc" in combined_text:
                charsadda_flag = True
            elif "peshawar division" in combined_text:
                # Charsadda is a settled district of Peshawar Division
                charsadda_flag = True
            elif record_data.get("charsadda_eligibility") == "yes":
                # Explicitly marked eligible
                charsadda_flag = True

        # 3. KP flag
        kp_flag = False
        if any(term in combined_text for term in [
            "khyber pakhtunkhwa", "kp domicile", "kpk", "kp students", "kp higher education",
            "kpef", "kpitb", "peshawar", "charsadda", "mardan", "swat", "abbottabad"
        ]) or record_data.get("kp_eligibility") == "yes":
            kp_flag = True

        # 4. Pakistan-wide KP eligible
        pakistan_wide = False
        if any(term in combined_text for term in ["all pakistan", "nationwide", "pakistani nationals", "across pakistan", "open to all pakistani"]):
            if not any(term in combined_text for term in ["punjab only", "sindh only", "balochistan only"]):
                pakistan_wide = True

        # 5. Target University Flag
        target_uni_flag = False
        if report_type == "public":
            if any(kw in combined_text for kw in PUBLIC_TARGET_KEYWORDS):
                target_uni_flag = True
        elif report_type == "private":
            if any(kw in combined_text for kw in PRIVATE_TARGET_KEYWORDS):
                target_uni_flag = True
        else: # both / general
            if any(kw in combined_text for kw in PUBLIC_TARGET_KEYWORDS + PRIVATE_TARGET_KEYWORDS):
                target_uni_flag = True

        return charsadda_flag, kp_flag, pakistan_wide, target_uni_flag, is_merged_only
