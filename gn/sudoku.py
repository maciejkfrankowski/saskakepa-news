"""Generator sudoku dnia: ta sama data -> te same plansze (deterministyczny seed)."""
from __future__ import annotations

import random

LEVELS = {"latwe": ("Łatwe", 40), "srednie": ("Średnie", 33), "trudne": ("Trudne", 28)}


def _solved(rng: random.Random) -> list[int]:
    """Pełna poprawna plansza: wzorzec bazowy + losowe permutacje zachowujące reguły."""
    def shuffled(values):
        values = list(values)
        rng.shuffle(values)
        return values

    rows = [band * 3 + row for band in shuffled(range(3)) for row in shuffled(range(3))]
    cols = [stack * 3 + col for stack in shuffled(range(3)) for col in shuffled(range(3))]
    digits = shuffled(range(1, 10))
    return [digits[(3 * (r % 3) + r // 3 + c) % 9] for r in rows for c in cols]


def _candidates(grid: list[int], index: int) -> list[int]:
    row, col = divmod(index, 9)
    box = (row // 3) * 27 + (col // 3) * 3
    used = {grid[row * 9 + i] for i in range(9)} | {grid[i * 9 + col] for i in range(9)}
    used |= {grid[box + r * 9 + c] for r in range(3) for c in range(3)}
    return [d for d in range(1, 10) if d not in used]


def count_solutions(grid: list[int], limit: int = 2) -> int:
    """Liczy rozwiązania (do `limit`) – backtracking od pola z najmniejszą liczbą kandydatów."""
    best, options = -1, None
    for index, value in enumerate(grid):
        if value:
            continue
        found = _candidates(grid, index)
        if not found:
            return 0
        if options is None or len(found) < len(options):
            best, options = index, found
            if len(found) == 1:
                break
    if options is None:
        return 1
    total = 0
    for digit in options:
        grid[best] = digit
        total += count_solutions(grid, limit - total)
        grid[best] = 0
        if total >= limit:
            break
    return total


def generate(seed: str, clues: int) -> tuple[str, str]:
    """Zwraca (plansza, rozwiązanie) jako 81-znakowe teksty; 0 = puste pole.

    Usuwa pola, dopóki rozwiązanie pozostaje jednoznaczne i nie spadniemy poniżej `clues`.
    """
    rng = random.Random(seed)
    solution = _solved(rng)
    puzzle = solution[:]
    order = list(range(81))
    rng.shuffle(order)
    left = 81
    for index in order:
        if left <= clues:
            break
        keep, puzzle[index] = puzzle[index], 0
        if count_solutions(puzzle[:]) == 1:
            left -= 1
        else:
            puzzle[index] = keep
    return "".join(map(str, puzzle)), "".join(map(str, solution))


def daily(day: str) -> dict:
    levels = []
    for slug, (name, clues) in LEVELS.items():
        puzzle, solution = generate(f"{day}:{slug}", clues)
        levels.append({"slug": slug, "name": name, "puzzle": puzzle, "solution": solution})
    return {"date": day, "levels": levels}
