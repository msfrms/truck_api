from enum import Enum


class Error(str, Enum):
    USER_NOT_EXISTS = "user_not_exists"
    USER_ALREADY_EXISTS = "user_already_exists"
    NOT_ENOUGH_MONEY = "not_enough_money_on_balance"
    INCORRECT_EMAIL_OR_PASSOWRD = "incorrect_email_or_passord"
    NOT_ALLOW_OPERATION = "not_allow_used"
    CHANGE_STATUS_NOT_ALLOWED = "change_status_not_allowed"
    ORDER_ALREADY_IN_PROGRESS = "order_already_in_progress"
    ACCESS_DENIED = "access_denied"
    VIN_ALREADY_EXISTS_IN_ORDER = "vin_already_exists_in_order"
    CANCEL_ORDER_NOT_ALLOWED = "cancel_order_not_allowed"
