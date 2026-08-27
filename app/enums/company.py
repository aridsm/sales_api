from enum import IntEnum


class CompanyPermission(IntEnum):
    VIEW = 1
    VIEW_EDIT = 2
    ADMIN = 3


class InvitationStatus(IntEnum):
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3
