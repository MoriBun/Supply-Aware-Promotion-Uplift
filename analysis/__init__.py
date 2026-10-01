"""Week-5 analysis: evaluation of policies and uplift scores on simulator output (docs/phan_cong.md S5).

Nothing in ``sim/`` imports this package (decisions T-13). ``hidden/`` tables are
ground truth for evaluation only and are never joined into training data
(docs/schema.md): :func:`analysis.io.load_run` therefore never returns them;
use :func:`analysis.io.load_hidden` explicitly when evaluating.
"""
