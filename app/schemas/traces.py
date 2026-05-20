"""Layer 8 SystemTrace schema.

Purpose: define the trace record emitted after request completion for
observability and deterministic evaluation replay. Constraints: trace emission
must be non-blocking, include registry version, and avoid in-process
aggregation.
"""


class SystemTrace:
    """Placeholder for the Layer 8 request trace schema."""

    def __init__(self) -> None:
        raise NotImplementedError("SystemTrace schema is not implemented yet.")
