from app.seed import DEFAULT_SEED_PATH, load_seed_file


def test_sample_seed_file_is_valid() -> None:
    events = load_seed_file(DEFAULT_SEED_PATH)
    assert len(events) >= 8
    assert len({e.slug for e in events}) == len(events)


def test_sample_seed_is_not_marked_verified() -> None:
    # Sample data must stay unverified until checked against the organizer's page.
    assert all(e.last_verified_at is None for e in load_seed_file(DEFAULT_SEED_PATH))


def test_events_with_registration_link_point_to_http_urls() -> None:
    for event in load_seed_file(DEFAULT_SEED_PATH):
        if event.registration_url is not None:
            assert event.registration_url.scheme in {"http", "https"}
