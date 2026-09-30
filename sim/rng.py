"""Keyed random streams for common random numbers (docs/spec.md §5).

Every random draw goes through ``rng.rng_for(stream, *key)``. A generator is a
pure function of (seed, stream, key), so switching policy cannot shift the
random numbers of any session, order, driver or (cell, slot).
"""

from __future__ import annotations

import enum
import hashlib
import operator
import struct

import numpy as np


class Stream(enum.IntEnum):
    """Random streams. The integer codes are part of the CRN contract: never renumber."""

    WORLD = 1          # cell weights, riders, drivers; seeded by world_seed, not run_seed
    DEMAND = 2         # key (day, tick_of_day, cell): Poisson session counts
    SESSION = 3        # key (session_id): rider, destination, pre-drawn uniforms
    CELLSLOT = 4       # key (kind, cell_or_cluster, slot_or_block): legacy epsilon, switchback
    RIDER = 5          # key (rider_id): arm of rider-level A/B
    DRIVER = 6         # key (driver_id, counter): repositioning
    SESSION_BATCH = 7  # key (day, tick_of_day, cell): optional batched SESSION draws


_INT64 = struct.Struct("<q")


def hash64(*values: int) -> int:
    """Stable 64-bit hash of a tuple of integers (same on every process and platform)."""
    try:
        packed = b"".join(_INT64.pack(operator.index(v)) for v in values)
    except struct.error as exc:
        raise ValueError(f"key values must fit in int64: {values!r}") from exc
    return int.from_bytes(hashlib.blake2b(packed, digest_size=8).digest(), "little")


class Rng:
    """Factory of keyed generators for one run.

    ``WORLD`` streams are seeded by ``world_seed`` so the world (cell weights,
    riders, drivers) is identical across run seeds; every other stream is
    seeded by ``run_seed``.
    """

    def __init__(self, run_seed: int, world_seed: int) -> None:
        self.run_seed = operator.index(run_seed)
        self.world_seed = operator.index(world_seed)

    @classmethod
    def from_config(cls, cfg) -> Rng:
        return cls(run_seed=cfg.meta.run_seed, world_seed=cfg.meta.world_seed)

    def rng_for(self, stream: Stream, *key: int) -> np.random.Generator:
        """Independent generator for ``(stream, *key)``; keys must be integers."""
        stream = Stream(stream)
        if not key:
            raise ValueError(f"{stream.name}: a stream needs a non-empty key")
        seed = self.world_seed if stream is Stream.WORLD else self.run_seed
        return np.random.Generator(np.random.Philox(key=hash64(seed, stream.value, *key)))
