import pytest

from app.engine import verify_title
from tests.fake_store import load_sample_store


@pytest.fixture
def store():
    return load_sample_store()


def test_exact_duplicate_rejected(store):
    r = verify_title("The Indian Express", "English", "Daily", store)
    assert r.status == "REJECTED"


def test_phonetic_variation_rejected(store):
    r = verify_title("Namascar Bharat", "Hindi", "Weekly", store)
    assert r.status == "REJECTED"
    assert any(m.title == "Namaskar Bharat" for m in r.matches)


def test_disallowed_word_rejected(store):
    r = verify_title("Delhi Police Times", "English", "Daily", store)
    assert r.status == "REJECTED"
    assert any(v.type == "DISALLOWED_WORD" for v in r.violations)


def test_title_combination_rejected(store):
    r = verify_title("Hindu Indian Express", "English", "Daily", store)
    assert r.status == "REJECTED"
    assert any(v.type == "TITLE_COMBINATION" for v in r.violations)


def test_title_combination_with_phonetic_misspellings_rejected(store):
    r = verify_title("Hinduw Indien Expres", "English", "Daily", store)
    assert r.status == "REJECTED"
    assert any(v.type == "TITLE_COMBINATION" for v in r.violations)


def test_periodicity_modification_rejected(store):
    r = verify_title("Indian Express Daily", "English", "Daily", store)
    assert r.status == "REJECTED"
    assert any(v.type == "PERIODICITY_MODIFICATION" for v in r.violations)


def test_trivial_affix_rejected(store):
    r = verify_title("News Sakal", "Marathi", "Daily", store)
    assert r.status == "REJECTED"
    assert any(v.type == "DISALLOWED_AFFIX" for v in r.violations)


def test_cross_language_meaning_rejected(store):
    r = verify_title("Pratidin Sandhya", "Hindi", "Daily", store)
    assert r.status == "REJECTED"
    assert any(m.title == "Daily Evening" for m in r.matches)


def test_novel_title_not_rejected(store):
    r = verify_title("Coastal Voyager Digest", "English", "Weekly", store)
    assert r.status != "REJECTED"
    assert r.verification_score > 0


def test_pending_application_blocks_later_duplicate(store):
    first = verify_title("Sunrise Chronicle", "English", "Daily", store)
    assert first.status != "REJECTED"

    second = verify_title("Sunrise Chronicle", "English", "Daily", store)
    assert second.status == "REJECTED"
    assert any(m.source == "PENDING_APPLICATION" for m in second.matches)


def test_verification_score_matches_similarity_formula(store):
    r = verify_title("Completely Original Publication Name", "English", "Monthly", store)
    top_score = max((m.score for m in r.matches), default=0.0)
    assert r.verification_score == pytest.approx(max(0.0, 100.0 - top_score), abs=0.01)
