from enum import IntEnum


class TransferStatus(IntEnum):
    """Transfer states statuses."""
    ACTIVE = 1
    CONFIRMED = 2
    IGNORED = 3
