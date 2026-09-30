"""CRN streams (docs/spec.md §5, docs/plan.md P0) and hard rule 4 (no global randomness)."""

import ast
from pathlib import Path

import numpy as np
import pytest

from sim.rng import Rng, Stream, hash64

SIM_DIR = Path(__file__).resolve().parents[1] / "sim"


def draws(rng, stream, *key, n=5):
    return rng.rng_for(stream, *key).random(n)


def test_same_key_same_numbers():
    a, b = Rng(run_seed=3, world_seed=7), Rng(run_seed=3, world_seed=7)
    for stream in Stream:
        np.testing.assert_array_equal(draws(a, stream, 1, 2), draws(b, stream, 1, 2))


def test_different_key_different_numbers():
    rng = Rng(run_seed=0, world_seed=0)
    base = draws(rng, Stream.SESSION, 12345)
    assert not np.array_equal(base, draws(rng, Stream.SESSION, 12346))
    # Same values in a different key layout must not collide either.
    assert not np.array_equal(draws(rng, Stream.DEMAND, 1, 2), draws(rng, Stream.DEMAND, 2, 1))
    assert not np.array_equal(draws(rng, Stream.DEMAND, 1, 2), draws(rng, Stream.DEMAND, 1, 2, 0))


def test_different_stream_different_numbers():
    rng = Rng(run_seed=0, world_seed=0)
    seen = {tuple(draws(rng, stream, 42)) for stream in Stream}
    assert len(seen) == len(Stream)


def test_draws_do_not_depend_on_call_order():
    # CRN: what other sessions draw (and in which order) must not matter.
    rng = Rng(run_seed=1, world_seed=1)
    first = draws(rng, Stream.SESSION, 7)
    for sid in range(100):
        rng.rng_for(Stream.SESSION, sid).random(10)
    np.testing.assert_array_equal(first, draws(rng, Stream.SESSION, 7))


def test_world_stream_ignores_run_seed():
    a, b = Rng(run_seed=0, world_seed=99), Rng(run_seed=1, world_seed=99)
    np.testing.assert_array_equal(draws(a, Stream.WORLD, 0), draws(b, Stream.WORLD, 0))
    assert not np.array_equal(draws(a, Stream.SESSION, 0), draws(b, Stream.SESSION, 0))


def test_world_seed_only_changes_world_stream():
    a, b = Rng(run_seed=0, world_seed=1), Rng(run_seed=0, world_seed=2)
    assert not np.array_equal(draws(a, Stream.WORLD, 0), draws(b, Stream.WORLD, 0))
    np.testing.assert_array_equal(draws(a, Stream.SESSION, 0), draws(b, Stream.SESSION, 0))


def test_numpy_integer_keys_equal_python_ints():
    rng = Rng(run_seed=0, world_seed=0)
    np.testing.assert_array_equal(
        draws(rng, Stream.DRIVER, 5, 2), draws(rng, Stream.DRIVER, np.int64(5), np.int16(2))
    )


@pytest.mark.parametrize("key", [(1.0,), ("1",), (2**63,)])
def test_bad_keys_rejected(key):
    with pytest.raises((TypeError, ValueError)):
        Rng(0, 0).rng_for(Stream.SESSION, *key)


def test_empty_key_rejected():
    with pytest.raises(ValueError):
        Rng(0, 0).rng_for(Stream.SESSION)


def test_from_config(tiny_cfg):
    rng = Rng.from_config(tiny_cfg)
    assert (rng.run_seed, rng.world_seed) == (tiny_cfg.meta.run_seed, tiny_cfg.meta.world_seed)


def test_hash64_is_pinned():
    # Changing the hash silently changes every random number, so generated
    # datasets would no longer be reproducible. Update only on purpose and log
    # the change in docs/decisions.md.
    assert hash64(0, 3, 42) == 16375947467241191322
    assert hash64(20260930, 1, 0) == 12381375145982931506


# --- hard rule 4: no global numpy / stdlib randomness in sim/ ----------------

_ALLOWED_NP_RANDOM = {"Generator"}          # type hints anywhere
_ALLOWED_NP_RANDOM_IN_RNG = {"Philox"}      # only sim/rng.py builds bit generators


def random_violations(source: str, is_rng_module: bool = False) -> list[str]:
    allowed = _ALLOWED_NP_RANDOM | (_ALLOWED_NP_RANDOM_IN_RNG if is_rng_module else set())
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [f"import {a.name}" for a in node.names
                      if a.name == "random" or a.name.startswith("numpy.random")]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "random" or module.startswith("numpy.random") or (
                module == "numpy" and any(a.name == "random" for a in node.names)
            ):
                found.append(f"from {module} import ...")
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "random"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id in {"np", "numpy"}
            and node.attr not in allowed
        ):
            found.append(f"np.random.{node.attr}")
    return found


def test_checker_catches_violations():
    bad = (
        "import random\n"
        "from numpy.random import default_rng\n"
        "import numpy as np\n"
        "x = np.random.rand(3)\n"
        "g = np.random.default_rng(0)\n"
        "np.random.seed(1)\n"
    )
    assert len(random_violations(bad)) == 5
    assert random_violations("import numpy as np\ndef f(g: np.random.Generator): ...\n") == []
    assert random_violations("import numpy as np\nb = np.random.Philox(key=1)\n") == ["np.random.Philox"]


@pytest.mark.parametrize("path", sorted(SIM_DIR.rglob("*.py")), ids=lambda p: p.relative_to(SIM_DIR).as_posix())
def test_no_global_randomness_in_sim(path):
    is_rng = path == SIM_DIR / "rng.py"
    assert random_violations(path.read_text(encoding="utf-8"), is_rng) == [], (
        "use rng.rng_for(stream, *key) (CLAUDE.md hard rule 4)"
    )
