def compute_interest_level(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_growth_velocity(values: list[float]) -> float:
    if len(values) < 4:
        return 0.0

    head = sum(values[:2]) / 2
    tail = sum(values[-2:]) / 2
    if head <= 0:
        return tail
    return ((tail - head) / head) * 100


def compute_final_score(interest_level: float, growth_velocity: float) -> float:
    return 0.6 * interest_level + 0.4 * growth_velocity
