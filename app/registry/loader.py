"""Layer 11 registry loader.

Purpose: load and validate versioned concept registry JSON before swapping the
active pointer. Constraints: load into a new object, validate before exposure,
and never mutate the active registry in place.
"""


def load_registry() -> None:
    """Load a versioned concept registry asset."""
    raise NotImplementedError("Layer 11 registry loading is not implemented yet.")
