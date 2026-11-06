from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.deps import get_today
from app.main import app
from app.seed import load_seed_file, seed_events

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "events.fixture.yaml"

TODAY = date(2026, 11, 6)
UPCOMING = [
    "vietnam-highlands-trail-by-utmb-2027",
    "bac-ninh-legacy-marathon-2027",
    "mang-den-ultra-trail-2027",
    "vietnam-trail-marathon-2027",
    "hcmc-marathon-2027",
    "tet-run-mien-nam-2027",
    "dalat-ultra-trail-2027",
    "manulife-danang-international-marathon-2027",
    "the-explorer-trail-2027",
]


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    seed_events(db, load_seed_file(FIXTURE_PATH))
    app.dependency_overrides[get_today] = lambda: TODAY
    yield TestClient(app)
    app.dependency_overrides.clear()


def _slugs(response_json: dict) -> list[str]:
    return [item["slug"] for item in response_json["items"]]


def test_list_returns_upcoming_events_in_date_order(client: TestClient) -> None:
    body = client.get("/v1/events").json()
    assert _slugs(body) == UPCOMING
    assert body["total"] == len(UPCOMING)
    assert body["next_cursor"] is None
    assert body["last_updated_at"] is not None


def test_include_past_adds_the_cancelled_2026_event(client: TestClient) -> None:
    body = client.get("/v1/events", params={"include_past": "true"}).json()
    assert body["total"] == len(UPCOMING) + 1
    assert _slugs(body)[0] == "vietnam-ultra-marathon-mai-chau-2026"
    assert body["items"][0]["status"] == "cancelled"


def test_pagination_walks_all_events_without_duplicates(client: TestClient) -> None:
    seen: list[str] = []
    cursor = None
    pages = 0
    while True:
        params: dict[str, object] = {"limit": 4}
        if cursor:
            params["cursor"] = cursor
        body = client.get("/v1/events", params=params).json()
        seen.extend(_slugs(body))
        pages += 1
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert seen == UPCOMING
    assert pages == 3


@pytest.mark.parametrize("query", ["da lat", "Đà Lạt", "ĐÀ LẠT", "dalat"])
def test_search_ignores_diacritics_and_case(client: TestClient, query: str) -> None:
    slugs = _slugs(client.get("/v1/events", params={"q": query}).json())
    assert "dalat-ultra-trail-2027" in slugs


def test_search_requires_every_word(client: TestClient) -> None:
    body = client.get("/v1/events", params={"q": "da lat marathon"}).json()
    assert body["items"] == []
    assert body["total"] == 0


def test_type_filter(client: TestClient) -> None:
    body = client.get("/v1/events", params={"type": "road"}).json()
    assert set(_slugs(body)) == {
        "bac-ninh-legacy-marathon-2027",
        "hcmc-marathon-2027",
        "tet-run-mien-nam-2027",
        "manulife-danang-international-marathon-2027",
    }


def test_distance_bucket_filter(client: TestClient) -> None:
    marathon = _slugs(client.get("/v1/events", params={"distance": "42"}).json())
    assert set(marathon) == {"hcmc-marathon-2027", "manulife-danang-international-marathon-2027"}
    ultra = _slugs(client.get("/v1/events", params={"distance": "ultra"}).json())
    assert set(ultra) == {"vietnam-trail-marathon-2027", "vietnam-highlands-trail-by-utmb-2027"}
    both = client.get("/v1/events", params=[("distance", "42"), ("distance", "ultra")]).json()
    assert both["total"] == 4


@pytest.mark.parametrize(
    "region,expected",
    [
        ("south", {"hcmc-marathon-2027", "tet-run-mien-nam-2027", "the-explorer-trail-2027"}),
        ("highlands", {"vietnam-highlands-trail-by-utmb-2027", "dalat-ultra-trail-2027"}),
    ],
)
def test_region_filter(client: TestClient, region: str, expected: set[str]) -> None:
    assert set(_slugs(client.get("/v1/events", params={"region": region}).json())) == expected


def test_open_only_filter(client: TestClient) -> None:
    body = client.get("/v1/events", params={"open_only": "true"}).json()
    assert _slugs(body) == ["vietnam-trail-marathon-2027"]


def test_date_range_filter(client: TestClient) -> None:
    body = client.get("/v1/events", params={"from": "2027-03-01", "to": "2027-03-31"}).json()
    assert set(_slugs(body)) == {
        "dalat-ultra-trail-2027",
        "manulife-danang-international-marathon-2027",
    }


def test_filters_combine(client: TestClient) -> None:
    params = {"type": "trail", "region": "highlands", "q": "highlands"}
    body = client.get("/v1/events", params=params).json()
    assert _slugs(body) == ["vietnam-highlands-trail-by-utmb-2027"]


@pytest.mark.parametrize(
    "params",
    [{"cursor": "garbage"}, {"limit": 0}, {"limit": 51}, {"type": "swim"}, {"distance": "99"}],
)
def test_invalid_parameters_are_rejected(client: TestClient, params: dict) -> None:
    assert client.get("/v1/events", params=params).status_code == 422


def test_detail_returns_distances_longest_first(client: TestClient) -> None:
    response = client.get("/v1/events/vietnam-trail-marathon-2027")
    assert response.status_code == 200
    body = response.json()
    assert [d["label"] for d in body["distances"]] == ["70K", "50K", "21K", "10K", "5K"]
    assert body["registration_url"].startswith("https://vietnamtrailseries.com/")
    assert body["verified"] is False
    assert body["status"] == "registration_open"


def test_detail_of_cancelled_event(client: TestClient) -> None:
    body = client.get("/v1/events/vietnam-ultra-marathon-mai-chau-2026").json()
    assert body["status"] == "cancelled"
    assert body["registration_url"] is None


def test_detail_unknown_slug_is_404(client: TestClient) -> None:
    assert client.get("/v1/events/does-not-exist").status_code == 404
