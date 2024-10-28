from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def list(cls):
        return [t.value for t in cls]


class SupportedMime(BaseEnum):
    jpg = 'image/jpg'
    jpeg = 'image/jpeg'
    png = 'image/png'

    def is_image_type(mime):
        if mime in self.list():
            return True
        return False


class UserType(BaseEnum):
    user = 'user'
