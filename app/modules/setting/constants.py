from enum import Enum


class SettingKey(str, Enum):
    INIT_DATA = "INIT_DATA"
    FILE_STORAGE = "FILE_STORAGE"
    SERVER = "SERVER"
    FILE_UPLOAD = "FILE_UPLOAD"
