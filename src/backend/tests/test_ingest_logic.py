from datetime import date

import pytest

from app.ingest.changes import decide, diff_event
from app.ingest.extract import EventCandidate, Evidence, verify_candidate
from app.ingest.normalize import (
    DistanceData,
    EventData,
    fold,
    normalize,
    normalize_distance,
    normalize_province,
    slugify,
)
from app.ingest.validate import validate
from app.models import Distance, Event, Source

TODAY = date(2026, 11, 6)
PAGE = """Vietnam Trail Marathon 2027
Ngày thi đấu: 16/01/2027   Địa điểm: Mộc Châu, Sơn La
Cự ly: 70K, 50K, 21K"""


def ev(quote: str, confidence: float = 0.9) -> Evidence:
    return Evidence(confidence=confidence, evidence=quote)


def candidate(**overrides: object) -> EventCandidate:
    data: dict[str, object] = {
        "name": "Vietnam Trail Marathon 2027",
        "start_date": date(2027, 1, 16),
        "province": "Sơn La",
        "fields": {
            "name": ev("Vietnam Trail Marathon 2027"),
            "start_date": ev("Ngày thi đấu: 16/01/2027"),
            "province": ev("Mộc Châu, Sơn La"),
        },
    }
    data.update(overrides)
    return EventCandidate.model_validate(data)


def source(tier: int = 2, url: str = "https://vietnamtrailseries.com/sitemap.xml") -> Source:
    return Source(id="s", name="S", kind="sitemap", url=url, tier=tier)


# ---- evidence ----------------------------------------------------------------------------


def test_verified_fields_are_kept_with_their_confidence() -> None:
    result = verify_candidate(candidate(), PAGE)
    assert result.ok and result.dropped == []
    assert result.creation_confidence == 0.9


def test_quote_matching_ignores_whitespace_and_case() -> None:
    fields = {
        "name": ev("vietnam   TRAIL marathon 2027"),
        "start_date": ev("ngày thi đấu:\n16/01/2027"),
    }
    assert verify_candidate(candidate(fields=fields, province=None), PAGE).ok


def test_field_with_invented_evidence_is_dropped() -> None:
    fields = candidate().fields | {"province": ev("Lâm Đồng, Đà Lạt")}
    result = verify_candidate(candidate(fields=fields), PAGE)
    assert result.ok
    assert result.dropped == ["province"]
    assert result.candidate.province is None


def test_missing_evidence_for_a_required_field_rejects_the_candidate() -> None:
    fields = {"name": ev("Vietnam Trail Marathon 2027")}
    result = verify_candidate(candidate(fields=fields), PAGE)
    assert not result.ok and "start_date" in (result.reason or "")


def test_too_short_quote_does_not_count() -> None:
    fields = candidate().fields | {"name": ev("V")}
    assert not verify_candidate(candidate(fields=fields), PAGE).ok


# ---- normalization -----------------------------------------------------------------------


def test_fold_and_slug() -> None:
    assert fold("Đà Lạt") == "da lat"
    assert slugify("Dalat Ultra Trail", 2027) == "dalat-ultra-trail-2027"
    assert slugify("Giải Chạy Đà Nẵng 2027", 2027) == "giai-chay-da-nang-2027"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("TP.HCM", "TP. Hồ Chí Minh"),
        ("Ho Chi Minh", "TP. Hồ Chí Minh"),
        ("Tỉnh Lâm Đồng", "Lâm Đồng"),
        ("lam dong", "Lâm Đồng"),
        ("Hà Nội", "Hà Nội"),
        ("Somewhere New", "Somewhere New"),
        (None, None),
    ],
)
def test_province_normalization(raw: str | None, expected: str | None) -> None:
    assert normalize_province(raw) == expected


@pytest.mark.parametrize(
    "label,km,expected",
    [
        ("Full Marathon", 42.195, ("42K", 42.2)),
        ("42km", None, ("42K", 42.2)),
        ("Half", 21.0975, ("21K", 21.1)),
        ("70K", None, ("70K", 70.0)),
        ("12,5 km", None, ("12.5K", 12.5)),
        ("Kids run", None, None),
    ],
)
def test_distance_normalization(label: str, km: float | None, expected: tuple | None) -> None:
    assert normalize_distance(label, km) == expected


def test_normalize_builds_event_data() -> None:
    fields = candidate().fields | {
        "event_type": ev("Trail"),
        "status": ev("Ngày thi đấu"),
        "distances": ev("Cự ly: 70K, 50K, 21K"),
    }
    cand = candidate(
        fields=fields,
        event_type="Trail",
        status="weird",
        distances=[
            {"label": "42km", "distance_km": 42.195},
            {"label": "42K", "distance_km": 42.2},
            {"label": "5K"},
        ],
    )
    data = normalize(verify_candidate(cand, PAGE))
    assert data.slug == "vietnam-trail-marathon-2027"
    assert data.event_type == "trail" and data.status == "scheduled"
    assert [d.label for d in data.distances] == ["42K", "5K"]


# ---- validation --------------------------------------------------------------------------


def data(**overrides: object) -> EventData:
    base: dict[str, object] = {
        "slug": "x-2027", "name": "X", "start_date": date(2027, 1, 16), "event_type": "trail",
        "province": "Sơn La",
    }  # fmt: skip
    base.update(overrides)
    return EventData.model_validate(base)


def test_validation_blocks_implausible_dates() -> None:
    assert validate(data(start_date=date(2020, 1, 1)), source(), TODAY).blocking
    assert validate(data(start_date=date(2035, 1, 1)), source(), TODAY).blocking
    assert validate(data(end_date=date(2027, 1, 1)), source(), TODAY).blocking
    assert not validate(data(), source(), TODAY).blocking


def test_registration_link_host_must_match_official_source() -> None:
    ok = validate(data(registration_url="https://vietnamtrailseries.com/book"), source(), TODAY)
    assert ok.data.registration_url
    ticketing = validate(data(registration_url="https://irace.vn/su-kien/x"), source(), TODAY)
    assert ticketing.data.registration_url
    foreign = validate(data(registration_url="https://evil.example/pay"), source(), TODAY)
    assert foreign.data.registration_url is None and foreign.warnings
    listing = validate(data(registration_url="https://org.example/reg"), source(tier=3), TODAY)
    assert listing.data.registration_url  # tier 3 is always reviewed by a person anyway


def test_deadline_after_the_event_is_dropped() -> None:
    result = validate(data(registration_deadline=date(2027, 2, 1)), source(), TODAY)
    assert result.data.registration_deadline is None and result.warnings


# ---- policy ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind,field,tier,confidence,issues,expected",
    [
        ("create", None, 2, 0.9, False, "auto_applied"),
        ("create", None, 2, 0.9, True, "pending"),
        ("create", None, 2, 0.5, False, "pending"),
        ("create", None, 3, 0.99, False, "pending"),
        ("update", "organizer", 2, 0.9, False, "auto_applied"),
        ("update", "start_date", 2, 0.99, False, "pending"),
        ("update", "status", 1, 0.99, False, "pending"),
        ("update", "venue", 2, 0.5, False, "pending"),
        ("update", "organizer", 3, 0.99, False, "pending"),
    ],
)
def test_decision_policy(
    kind: str, field: str | None, tier: int, confidence: float, issues: bool, expected: str
) -> None:
    assert decide(kind, field, tier, confidence, 0.85, issues)[0] == expected


# ---- diff --------------------------------------------------------------------------------


def stored() -> Event:
    event = Event(
        slug="x-2027", name="X", event_type="trail", start_date=date(2027, 1, 16),
        province="Sơn La", status="registration_open", organizer="Topas",
    )  # fmt: skip
    event.distances = [
        Distance(label="70K", distance_km=70, fee_vnd=1_000_000),
        Distance(label="21K", distance_km=21),
    ]
    return event


def test_diff_ignores_same_values_and_never_blanks_known_ones() -> None:
    assert diff_event(stored(), data(status="scheduled", organizer=None)) == []


def test_diff_reports_changed_fields() -> None:
    changes = {c.field: c for c in diff_event(stored(), data(start_date=date(2027, 1, 17)))}
    assert set(changes) == {"start_date"}
    assert changes["start_date"].new == date(2027, 1, 17)


def test_distance_merge_keeps_existing_fee_and_detects_new_distance() -> None:
    new = data(
        distances=[
            DistanceData(label="70K", distance_km=70),
            DistanceData(label="50K", distance_km=50),
        ]
    )
    (change,) = diff_event(stored(), new)
    assert change.field == "distances"
    by_label = {d["label"]: d for d in change.new}
    assert by_label["70K"]["fee_vnd"] == 1_000_000
    assert "50K" in by_label and "21K" in by_label
