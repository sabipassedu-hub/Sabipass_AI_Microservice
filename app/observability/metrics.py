"""Layer 8 metrics emission.

Purpose: emit latency, fallback, execution path, and normalization status
metrics to a sidecar without blocking responses. Constraints: fire-and-forget
only, no in-process aggregation, and no shared memory between workers.
"""


def emit_metric() -> None:
    """Emit one observability metric."""
    raise NotImplementedError("Layer 8 metrics emission is not implemented yet.")
