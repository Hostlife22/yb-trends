from app.services.scoring import (
    ScoreWeights,
    YouTubeStats,
    compute_final_score,
    compute_growth_velocity,
    compute_interest_level,
    compute_search_demand,
    compute_search_momentum,
    compute_weighted_final_score,
    compute_youtube_demand,
    compute_youtube_freshness,
)


def test_interest_level_average() -> None:
    assert compute_interest_level([10, 20, 30]) == 20


def test_growth_velocity() -> None:
    value = compute_growth_velocity([10, 10, 20, 30])
    assert round(value, 2) == 150.0


def test_final_score() -> None:
    assert compute_final_score(50, 25) == 40.0


# ---------- New normalized sub-scores --------------------------------------


def test_search_demand_zero_when_no_interest() -> None:
    assert compute_search_demand(0.0) == 0.0
    assert compute_search_demand(-5.0) == 0.0


def test_search_demand_in_unit_interval() -> None:
    for raw in [1, 10, 50, 100, 500, 10_000]:
        v = compute_search_demand(float(raw))
        assert 0.0 <= v <= 1.0


def test_search_demand_monotonic() -> None:
    a = compute_search_demand(10.0)
    b = compute_search_demand(50.0)
    c = compute_search_demand(100.0)
    assert a < b < c


def test_search_momentum_flat_is_half() -> None:
    assert compute_search_momentum(0.0) == 0.5


def test_search_momentum_bounds() -> None:
    assert compute_search_momentum(10_000.0) <= 1.0
    assert compute_search_momentum(-10_000.0) >= 0.0


def test_youtube_demand_zero_when_no_views() -> None:
    assert compute_youtube_demand(YouTubeStats()) == 0.0


def test_youtube_demand_monotonic() -> None:
    low = compute_youtube_demand(YouTubeStats(median_views=1_000))
    mid = compute_youtube_demand(YouTubeStats(median_views=100_000))
    high = compute_youtube_demand(YouTubeStats(median_views=1_000_000))
    assert low < mid < high


def test_youtube_freshness_requires_both_volume_and_diversity() -> None:
    # 100 videos but a single channel posting them all → not fresh
    one_channel_spam = compute_youtube_freshness(
        YouTubeStats(videos_published=100, channels_count=1)
    )
    # Same volume across many channels → highly fresh
    healthy = compute_youtube_freshness(
        YouTubeStats(videos_published=20, channels_count=10)
    )
    assert one_channel_spam < healthy
    assert 0.0 <= one_channel_spam <= 1.0
    assert 0.0 <= healthy <= 1.0


def test_youtube_freshness_zero_when_empty() -> None:
    assert compute_youtube_freshness(YouTubeStats()) == 0.0


def test_weighted_final_score_default_weights() -> None:
    score = compute_weighted_final_score(
        search_demand=1.0,
        search_momentum=1.0,
        youtube_demand=1.0,
        youtube_freshness=1.0,
    )
    assert round(score, 4) == 1.0


def test_weighted_final_score_zero_inputs() -> None:
    score = compute_weighted_final_score(
        search_demand=0.0,
        search_momentum=0.0,
        youtube_demand=0.0,
        youtube_freshness=0.0,
    )
    assert score == 0.0


def test_weighted_final_score_custom_weights() -> None:
    weights = ScoreWeights(
        search_demand=1.0,
        search_momentum=0.0,
        youtube_demand=0.0,
        youtube_freshness=0.0,
    )
    score = compute_weighted_final_score(
        search_demand=0.7,
        search_momentum=0.0,
        youtube_demand=0.0,
        youtube_freshness=0.0,
        weights=weights,
    )
    assert round(score, 4) == 0.7
