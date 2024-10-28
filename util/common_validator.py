import re


EMAIL_PATTERN = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

def email_validator(email: str):
    pattern = re.compile(EMAIL_PATTERN)
    if pattern.match(email):
        return True
    return False
