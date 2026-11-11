import random

PAYOUT_TABLE = {
    1:  {1: 3.0},
    2:  {1: 1.0, 2: 9.0},
    3:  {1: 1.0, 2: 2.0, 3: 16.0},
    4:  {1: 0.5, 2: 2.0, 3: 6.0, 4: 12.0},
    5:  {1: 0.5, 2: 1.0, 3: 3.0, 4: 15.0, 5: 50.0},
    6:  {1: 0.5, 2: 1.0, 2: 2.0, 4: 3.0, 5: 30.0, 6: 75.0},
    7:  {1: 0.5, 2: 0.5, 3: 1.0, 4: 6.0, 5: 12.0, 6: 36.0, 7: 100.0},
    8:  {1: 0.5, 2: 0.5, 3: 1.0, 4: 3.0, 5: 6.0, 6: 19.0, 7: 90.0, 8: 720.0},
    9:  {1: 0.5, 2: 0.5, 3: 1.0, 4: 2.0, 5: 4.0, 6: 8.0, 7: 20.0, 8: 80.0, 9: 1200.0},
    10: {1: 0.5, 2: 0.5, 3: 1.0, 4: 2.0, 5: 3.0, 6: 5.0, 7: 10.0, 8: 30.0, 9: 600.0, 10: 1800.0}
}

def draw_numbers() -> list[int]:
    """Draws 20 unique random numbers from 1 to 80."""
    return sorted(random.sample(range(1, 81), 20))

def calculate_payout(spots: int, matches: int, bet_amount: float) -> tuple[float, float]:
    """Returns (multiplier, payout_amount)."""
    multiplier = PAYOUT_TABLE.get(spots, {}).get(matches, 0.0)
    return multiplier, bet_amount * multiplier

def format_grid(selected: set[int], drawn: set[int] = None) -> str:
    """Renders a text visualization of numbers."""
    if drawn is None:
        drawn = set()
    output = []
    sorted_sel = sorted(list(selected))
    for num in sorted_sel:
        if num in drawn:
            output.append(f"🟢 {num:02d}")  # Hit
        else:
            output.append(f"⚪ {num:02d}")  # Picked
    return " | ".join(output) if output else "None"
