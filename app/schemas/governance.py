"""Layer 10 review queue event schema.

Purpose: define events sent to human governance for alias review, content gaps,
normalization failures, and escape-valve audits. Constraints: events must be
deduplicable, non-blocking, and unable to mutate registry assets directly.
"""


class ReviewQueueEvent:
    """Placeholder for the Layer 10 governance event schema."""

    def __init__(self) -> None:
        raise NotImplementedError("ReviewQueueEvent schema is not implemented yet.")
