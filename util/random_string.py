import string
import random


def get_crypto_rand_string(length: int = 32) -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(length)
    )

