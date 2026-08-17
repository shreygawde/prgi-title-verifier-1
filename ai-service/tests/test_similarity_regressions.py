from app.rules import SIMILARITY_DISPLAY_THRESHOLD
from app.similarity import compare_titles


def test_namascar_bharat_remains_a_strong_phonetic_match():
    result = compare_titles("Namascar Bharat", "Namaskar Bharat")

    assert result.score >= 85
    assert "PHONETIC" in result.match_types


def test_unrelated_titles_do_not_get_a_high_phonetic_match():
    result = compare_titles("phone news agency", "Financial Express")

    assert result.score < 80
    assert "PHONETIC" not in result.match_types


def test_clearly_unrelated_titles_do_not_get_high_phonetic_similarity():
    result = compare_titles("Silver Meadow", "Crimson Harbor")

    assert result.score < SIMILARITY_DISPLAY_THRESHOLD
    assert "PHONETIC" not in result.match_types


def test_single_word_phonetic_variation_remains_strong():
    result = compare_titles("color", "colour")

    assert result.score >= 85
    assert "PHONETIC" in result.match_types


def test_generic_overlap_does_not_create_a_misleading_displayed_match():
    jansatta = compare_titles("General press daily", "Jansatta")
    evening = compare_titles("General press daily", "Daily Evening")

    assert jansatta.score < SIMILARITY_DISPLAY_THRESHOLD
    assert evening.score < SIMILARITY_DISPLAY_THRESHOLD
    assert not jansatta.match_types
    assert not evening.match_types


def test_midrange_similarity_is_labeled_fuzzy():
    result = compare_titles("Alpha Beacon", "Alpha Falcon")

    assert SIMILARITY_DISPLAY_THRESHOLD <= result.score < 60
    assert result.match_types == ["FUZZY"]


def test_exact_duplicate_remains_100_percent():
    result = compare_titles("Daily News", "Daily News")

    assert result.score == 100
    assert "EXACT_OR_NEAR_EXACT" in result.match_types
