from enum import Enum


class TimeInterval(Enum):
    one_min = '1 min'
    five_minutes = '5 mins'
    fifteen_minutes = '15 mins'
    one_hour = '1 hour'
    one_day = '1 day'


class TaskStatus(Enum):
    active = 'Active'
    disabled = 'Disabled'
