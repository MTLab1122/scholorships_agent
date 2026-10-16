import pytest
from agent.classifier import UniversityClassifier


@pytest.fixture
def classifier():
    return UniversityClassifier()


def test_imsciences_is_public_sector(classifier):
    """Crucial requirement: IMSciences must be classified as public-sector."""
    assert classifier.classify_university_name("Institute of Management Sciences Peshawar") == "public"
    assert classifier.classify_university_name("IMSciences Peshawar") == "public"
    assert classifier.classify_university_name("imsciences financial aid notice") == "public"


def test_public_universities(classifier):
    assert classifier.classify_university_name("University of Peshawar") == "public"
    assert classifier.classify_university_name("UET Peshawar") == "public"
    assert classifier.classify_university_name("Bacha Khan University Charsadda") == "public"
    assert classifier.classify_university_name("Islamia College Peshawar") == "public"
    assert classifier.classify_university_name("Khyber Medical University") == "public"


def test_private_universities(classifier):
    assert classifier.classify_university_name("Abasyn University Peshawar") == "private"
    assert classifier.classify_university_name("CECOS University") == "private"
    assert classifier.classify_university_name("Iqra National University") == "private"
    assert classifier.classify_university_name("City University Peshawar") == "private"
    assert classifier.classify_university_name("Sarhad University") == "private"


def test_charsadda_flag_explicit_and_bkuc(classifier):
    data = {
        "name": "District Charsadda Need Based Aid",
        "sponsor": "Bacha Khan University Charsadda",
        "district_requirements": "Charsadda",
        "charsadda_eligibility": "yes"
    }
    charsadda, kp, pak, target, merged = classifier.calculate_priority_flags(data, "public")
    assert charsadda is True
    assert kp is True
    assert merged is False


def test_merged_districts_does_not_set_charsadda_flag(classifier):
    """Charsadda is a settled district of Peshawar Division. It is NOT an ex-FATA merged district."""
    data = {
        "name": "Merged Districts Only Special Scholarship",
        "sponsor": "Directorate of Merged Areas",
        "domicile_requirements": "Ex-FATA merged districts only (Bajaur, Mohmand, Khyber, Kurram)",
        "other_conditions": "For merged districts only",
        "charsadda_eligibility": "no"
    }
    charsadda, kp, pak, target, merged = classifier.calculate_priority_flags(data, "public")
    assert merged is True
    assert charsadda is False  # Must not set Charsadda flag!


def test_target_uni_flags(classifier):
    # Public report target: UoP or UET Peshawar
    data_uop = {"eligible_institutions": "University of Peshawar (UoP)"}
    _, _, _, target_pub, _ = classifier.calculate_priority_flags(data_uop, report_type="public")
    assert target_pub is True

    # Private report target: Abasyn University Peshawar
    data_abasyn = {"eligible_institutions": "Abasyn University Peshawar"}
    _, _, _, target_priv, _ = classifier.calculate_priority_flags(data_abasyn, report_type="private")
    assert target_priv is True
