from enum import Enum

class UpdateOperation(Enum):
    """
    Enum defining allowed update operations for flexible schema modifications.
    
    Attributes:
        SET: Update or insert field value ($set operator)
        PUSH: Append to array field ($push operator)
        PUSH_BOUNDED: Append to array and maintain max size via $slice
        UNSET: Remove field from document ($unset operator)
        INC: Increment numeric field ($inc operator)
        CURRENT_DATE: Update field with current timestamp ($currentDate operator)
        SET_ON_INSERT: Set field only on document insertion ($setOnInsert operator)
    """
    SET = "$set"
    PUSH = "$push"
    PUSH_BOUNDED = "$push_bounded"  # Custom: $push with $slice
    UNSET = "$unset"
    INC = "$inc"
    CURRENT_DATE = "$currentDate"
    SET_ON_INSERT = "$setOnInsert"

