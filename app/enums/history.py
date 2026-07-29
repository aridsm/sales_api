from enum import IntEnum

class ActionType(IntEnum):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    CANCEL = 4

class EntityType(IntEnum):
    PRODUCT = 1
    CATEGORY = 2
    SALE = 3
    OTHER_EXPENSE = 4
    STOCK_ENTRY = 5
