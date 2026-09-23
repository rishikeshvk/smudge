from math import sqrt

Z_95 = 1.959964


def wilson_interval(
    successes: int, trials: int, z: float = Z_95
) -> tuple[float, float]:
    """95% interval for a rate; unlike the normal approximation it works at 0 of n."""
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    denominator = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denominator
    margin = z * sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)
