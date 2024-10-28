import hmac, hashlib
import uuid
import bcrypt

def string_to_binary(string):
    binary_array = bytearray()
    binary_array.extend(map(ord, string))
    return binary_array


def hash_hmac_sha256(secret, message):
    m = hmac.new(
        string_to_binary(secret),
        message.encode(),
        hashlib.sha256
    )
    return m.hexdigest()


def hash_sha256(message):
    return hashlib.sha256(message.encode()).hexdigest()

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
