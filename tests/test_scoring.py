from app.services.scoring import compute_final_score, compute_growth_velocity, compute_interest_level


def test_interest_level_average() -> None:
    assert compute_interest_level([10, 20, 30]) == 20


def test_growth_velocity() -> None:
    value = compute_growth_velocity([10, 10, 20, 30])
    assert round(value, 2) == 150.0


def test_final_score() -> None:
    assert compute_final_score(50, 25) == 40.0
