from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_similarity_returns_scores_for_each_candidate():
    r = client.post(
        "/similarity",
        json={
            "title": "Example Newspaper",
            "candidates": ["Example News Paper", "Daily Example", "Example Times"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    titles = [m["title"] for m in body["matches"]]
    assert titles == ["Example News Paper", "Daily Example", "Example Times"]
    for match in body["matches"]:
        assert 0.0 <= match["fuzzy"] <= 1.0
        assert 0.0 <= match["phonetic"] <= 1.0


def test_similarity_near_duplicate_scores_high():
    r = client.post(
        "/similarity",
        json={"title": "Example Newspaper", "candidates": ["Example News Paper"]},
    )
    match = r.json()["matches"][0]
    assert match["fuzzy"] > 0.9


def test_similarity_phonetic_variant_scores_high_on_phonetic():
    r = client.post(
        "/similarity",
        json={"title": "Namaskar Bharat", "candidates": ["Namascar Bharat"]},
    )
    match = r.json()["matches"][0]
    assert match["phonetic"] == 1.0


def test_similarity_empty_candidates_returns_empty_matches():
    r = client.post("/similarity", json={"title": "Anything", "candidates": []})
    assert r.status_code == 200
    assert r.json()["matches"] == []
