from random import choices, randint
from string import ascii_uppercase, digits
from urllib import parse

def otpgen():
    otp = ""
    for i in range(7):
        otp += str(randint(1, 9))
    return otp
