"""Bounded, deterministic sampling of column values using reservoir sampling."""
import random
from dataclasses import dataclass

from privexis.connectors import iter_tables


@dataclass
class ColumnSample:
    source: str
    table: str
    column: str
    values: list        # at most k non-empty values, as stripped strings
    non_empty: int      # how many non-empty values the column had in total


def sample_path(path, k: int = 50, seed: int = 42) -> list:
    """Return one ColumnSample per column in every table of the file."""
    results = []
    for table in iter_tables(path):
        rng = random.Random(seed)            # own RNG: no hidden global state
        n = len(table.columns)
        reservoirs = [[] for _ in range(n)]
        seen = [0] * n

        for row in table.rows:               # single pass over the data
            for i, raw in enumerate(row[:n]):  # [:n] guards against ragged rows
                if raw is None:
                    continue
                v = str(raw).strip()
                if v == "":
                    continue
                seen[i] += 1
                if len(reservoirs[i]) < k:
                    reservoirs[i].append(v)
                else:
                    j = rng.randint(0, seen[i] - 1)
                    if j < k:                # replace with probability k / seen
                        reservoirs[i][j] = v

        for i, col in enumerate(table.columns):
            results.append(ColumnSample(table.source, table.name, col,
                                        reservoirs[i], seen[i]))
    return results