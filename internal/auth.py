from datetime import datetime, timedelta, timezone
import pytz
import requests
from tomlkit import date
# from model import User, Skill
from model import User
from model.db import db
from system.authentication_jwt import encode_access_token
from system.error_code import ERROR_CODE
from system.exceptions import ApplicationError
from util import common
from sqlalchemy import desc, func
# from services.mail import mail_service
import time, jwt, os, random, string
# from services import sendgrid
from util.response import response_error
from services.automation import *

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def create_user(data):
    try:
        # check if email is existed
        existed_user = db.session.query(User).filter(func.lower(User.email) == data['email']).first()
        if existed_user: return None, ERROR_CODE['EMAIL_IS_EXISTED']

        user = User(
            email=data['email'],
            username=data['email'].split('@')[0],
            password=data['password'],
            first_name=data.get('first_name'),
            sur_name=data.get('sur_name'),
            current_position=data.get('current_position'),
            level=data.get('level'),
            work_place=data.get('work_place'),
        )

        skills = data.get('skills')
        if skills:
            existing_skills = db.session.query(Skill).filter(Skill.name.in_(skills)).all()
            existing_skill_names = {skill.name for skill in existing_skills}
            new_skill_names = set(skills) - existing_skill_names
            new_skills = [Skill(name=skill_name) for skill_name in new_skill_names]
            db.session.add_all(new_skills)
            all_skills = existing_skills + new_skills
        else:
            all_skills = []

        user.skills = all_skills
        db.session.add(user)
        db.session.commit()
        webhook_data = {
            "created_at": datetime.now(pytz.timezone('Etc/GMT-7')).strftime('%Y-%m-%d %H:%M:%S'),
            "sur_name": user.sur_name,
            "first_name": user.first_name,
            "email": user.email,
        }

        if os.environ.get("ENV") == "PRODUCT":
            _, err = AutomationApiHandler.call("post", WEBHOOK_SLUG["CREATE_USER"], webhook_data)
            if err:
                return None, err

        return { **user.serialize(), 'access_token': encode_access_token(user.user_id) }, None
    except ApplicationError as err:
        common.push_log_to_sentry(message='Create user failed', 
        extra_data={
            'payload': data,
            'error': str(err)
        })
        return None, err



# def create_user_and_send_otp(data):
#     try:
#         # check if email is existed
#         existed_user = (
#             db.session.query(User)
#             .filter(func.lower(User.email) == data["email"])
#             .first()
#         )
#         if existed_user:
#             return None, ERROR_CODE["EMAIL_IS_EXISTED"]
#         #Create new user entry into database
#         user = User(
#             email=data["email"],
#             username=data["email"].split("@")[0],
#             password=data["password"],
#             first_name=data.get("first_name"),
#             sur_name=data.get("sur_name"),
#             current_position=data.get("current_position"),
#             level=data.get("level"),
#             work_place=data.get("work_place"),
#         )

#         skills = data.get("skills")
#         if skills:
#             existing_skills = (
#                 db.session.query(Skill).filter(Skill.name.in_(skills)).all()
#             )
#             existing_skill_names = {skill.name for skill in existing_skills}
#             new_skill_names = set(skills) - existing_skill_names
#             new_skills = [Skill(name=skill_name) for skill_name in new_skill_names]
#             db.session.add_all(new_skills)
#             all_skills = existing_skills + new_skills
#         else:
#             all_skills = []

#         user.skills = all_skills
#         #generate OTP code
#         user.otp = generate_otp()
#         user.otp_date = datetime.utcnow()
#         db.session.add(user)
#         db.session.commit()
#         # response = sendgrid.send_otp(user.email, user.otp)
#         if response.status_code != 202:
#             return None, ERROR_CODE["SEND_OTP_FAILED"]
        
#         return "OTP SENT SUCCESSFULLY", None
#     except ApplicationError as err:
#         common.push_log_to_sentry(
#             message="Create user failed",
#             extra_data={"payload": data, "error": str(err)},
#         )
#         return None, err


def verify_otp(data):
    otp = data["otp"]
    email = data["email"]
    user: User = db.session.query(User).filter(User.email == email).first()
    if not user:
        return None, ERROR_CODE["USER_NOT_FOUND"]
    if user.otp != otp:
        return None, ERROR_CODE["OTP_IS_INVALID"]
    elif (datetime.utcnow() - user.otp_date).seconds > 120:
        print((datetime.utcnow() - user.otp_date).seconds)
        return None, ERROR_CODE["OTP_IS_EXPIRED"]

    webhook_data = {
            "created_at": datetime.now(pytz.timezone('Etc/GMT-7')).strftime('%Y-%m-%d %H:%M:%S'),
            "sur_name": user.sur_name,
            "first_name": user.first_name,
            "email": user.email,
        }
    
    
    if os.environ.get("ENV") == "PRODUCT":
        _, err = AutomationApiHandler.call("post", WEBHOOK_SLUG["CREATE_USER"], webhook_data)
        if err:
            return None, err

    user.otp = None
    user.otp_date = None
    db.session.commit()
    return {**user.serialize(), "access_token": encode_access_token(user.user_id)}, None

def resend_otp(email):
    user: User = db.session.query(User).filter(User.email == email).first()
    if not user:
        return None, ERROR_CODE["USER_NOT_FOUND"]
    if user.otp and (datetime.utcnow() - user.otp_date).seconds < 120:
        return None, ERROR_CODE["OTP_IS_NOT_EXPIRED"]

    user.otp = generate_otp()
    user.otp_date = datetime.utcnow()
    db.session.commit()
    response = sendgrid.send_otp(user.email, user.otp)
    if response.status_code != 202:
        return None, ERROR_CODE["SEND_OTP_FAILED"]

    return "OTP SENT SUCCESSFULLY", None

def login(user: User, passwd):
    if user.check_password(passwd): 
        # user.last_login = datetime.now()
        if user.otp:
            return None, ERROR_CODE['EMAIL_NOT_VERIFIED']

        result = user.serialize()
        result['access_token'] = encode_access_token(user.user_id)

        return result, None

    # if unmatch password
    return None, ERROR_CODE["PASSWORD_IS_INVALID"]

def update_user_info(user: User, data):
    if 'phone_number' in data:
        user.phone_number = data['phone_number']
    if 'country' in data:
        user.country = data['country']
    if 'email' in data:
        user.email = data['email']
    if 'new_password' in data:
        user.password = data['new_password']
    if 'avatar_id' in data:
        user.avatar_id = data['avatar_id']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'sur_name' in data:
        user.sur_name = data['sur_name']
    db.session.commit()
    return user.serialize()

def generate_token():
    expiration_time = int(time.time()) + 3600  # 1 hour from now
    payload = {
        'exp': expiration_time, 
    }
    secret_key = os.getenv("SECRET_KEY") 
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

# def forgot_password(data):
#     if 'email' not in data:
#         return True, None  
    
#     user: User = db.session.query(User).\
#             filter(func.lower(User.email)==data["email"]).first()
#     if not user:
#         return None, ERROR_CODE['USER_NOT_FOUND']

#     token = generate_token()
#     user.forgot_password_key = token
#     db.session.commit()
#     mail_service.send_mail_reset_password(user.email, token)
#     return True, None

def is_token_expired(token, secret_key):
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
        expiration_time = decoded_token['exp']
        current_time = int(time.time())
        return current_time > expiration_time
    except jwt.ExpiredSignatureError or jwt.DecodeError:
        return True  # Token has expired or is invalid

def reset_password(data):
    try:
        user: User = db.session.query(User).\
                filter(User.forgot_password_key==data["token"]).first()
        if not user: return None, ERROR_CODE['TOKEN_IS_INVALID']
        
        secret_key = os.getenv("SECRET_KEY")
        if is_token_expired(data['token'], secret_key):
            return None, ERROR_CODE['TOKEN_IS_EXPIRED']
        
        # save new password
        user.password = data['password']
        user.forgot_password_key = None
        db.session.commit()
        return True, None
    except ApplicationError as err:
        common.push_log_to_sentry(message='Reset password fail', 
        extra_data={
            'payload': data,
            'error': str(err)
        })
        return None, err
