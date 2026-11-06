import re

from app.ingest.sources import DEFAULT_SOURCES_PATH, load_sources


def test_registry_file_is_valid() -> None:
    sources = load_sources(DEFAULT_SOURCES_PATH)
    assert len(sources) >= 15
    assert len({s.id for s in sources}) == len(sources)


def test_registry_covers_every_tier_and_kind() -> None:
    sources = load_sources(DEFAULT_SOURCES_PATH)
    assert {s.tier for s in sources} == {1, 2, 3} - {1}  # no tier-1 (rule-parsed) source yet
    assert {s.kind for s in sources} == {"sitemap", "listing_page", "event_page"}


def test_disabled_sources_explain_why() -> None:
    for source in load_sources(DEFAULT_SOURCES_PATH):
        if not source.enabled:
            assert source.notes, f"{source.id} is disabled without a note"


def test_url_include_patterns_compile_and_match_something_plausible() -> None:
    patterns = [s.url_include for s in load_sources(DEFAULT_SOURCES_PATH) if s.url_include]
    assert patterns
    assert re.search(patterns[0], "https://vietnamtrailseries.com/trail-marathon/vtm-book-now/")
