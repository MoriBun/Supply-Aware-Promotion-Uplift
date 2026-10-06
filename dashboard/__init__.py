"""Management dashboard of the simulator (FastAPI + React, no build step).

The package lives outside ``sim/`` and only *reads* the simulator: it builds the
world and the policy with the public factories, drives the same ten engine steps
through :mod:`dashboard.trace` (recording a frame per tick for the animation) and
reads the Parquet tables of finished experiments under ``runs/``. ``sim/`` never
imports from here (same rule as ``analysis/``).

Run with ``python -m dashboard`` (see ``dashboard/README.md``).
"""
