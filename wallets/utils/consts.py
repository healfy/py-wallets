from enum import IntEnum


class TransactionStatus(IntEnum):
    """Transaction states statuses."""
    UNDEFINED = 0
    NEW = 1
    NOT_FOUND = 2
    SUCCESSFUL = 3
    FAILED = 4
    PENDING = 5
    CONFIRMED = 6
    REPORTED = 7
    SENT = 8

    @classmethod
    def members_items(cls):
        return cls.__members__.items()
