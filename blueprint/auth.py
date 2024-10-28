from email import message
from turtle import update
from flask import Blueprint, request, jsonify
from voluptuous import REMOVE_EXTRA, All, Required, Schema, Optional, Lower, Msg, Length, validators
from model.user import User
from model.db import db
from flasgger.utils import swag_from
from system.error_code import ERROR_CODE
from util.response import response200, response_error
from internal import auth
from system.authentication_jwt import authorized, encode_access_token
# from model.file_upload import FileUpload
import uuid, os, random, string, jwt, requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from system.exceptions import ApplicationError

document_path = '../apidocs/apis/auth'

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

email_error = ERROR_CODE['EMAIL_INVALID']

SIGN_UP_WITH_EMAIL = Schema({
    Required('email', email_error): Msg(All(str, Lower), email_error),
    Required('password'): str,
    Optional('first_name'): str,
    Optional('sur_name'): str,
    Optional('skills'): [str],
    Optional('current_position'): str,
    Optional('level'): str,
    Optional('work_place'): str,
}, extra=REMOVE_EXTRA)

@bp.route("/sign-up", methods=["POST"])
@swag_from(f'''{document_path}/sign_up.yml''')
def sign_up():
    print("hihi")
    data = SIGN_UP_WITH_EMAIL(request.json)

    user, err = auth.create_user(data)

    if user:
        print("return user: ", user);
    else:
        print("return error", err);
    return err and response_error(err) or response200(user)


@bp.route("/sign-up/email-verify", methods=["POST"])
@swag_from(f"""{document_path}/sign_up_email_verify.yml""")
def sign_up_by_email():
    data = SIGN_UP_WITH_EMAIL(request.json)
    message, err = auth.create_user_and_send_otp(data)
    return err and response_error(err) or response200(message)

OTP_VERIFY = Schema({
    Required('otp'): str,
    Required('email'): All(str, Lower),
})

@bp.route("/otp-verify", methods=["POST"])
@swag_from(f"""{document_path}/sign_up_otp_verify.yml""")
def sign_up_otp_verify():
    data = OTP_VERIFY(request.json)
    user, err = auth.verify_otp(data)
    return err and response_error(err) or response200(user)

RESEND_OTP = Schema({
    Required('email'): All(str, Lower),
})

@bp.route("/resend-otp", methods=["POST"])
@swag_from(f"""{document_path}/resend_otp.yml""")
def resend_otp():
    data = RESEND_OTP(request.json)
    email = data['email']
    message, err = auth.resend_otp(email)
    return err and response_error(err) or response200(message)

USER_LOGIN = Schema({
    Required('email'): All(str, Lower),
    Required('password'): str,
})
@bp.route("/login", methods=["POST"])
@swag_from(f'''{document_path}/login.yml''')
def login():
    data = USER_LOGIN(request.json)

    user = None
    # get user with this email
    if data.get('email'):
        user = db.session.query(User).filter(User.email==data["email"]).first()

    if not user:
        return response_error(ERROR_CODE['USER_NOT_FOUND'])

    # check password
    result, error = auth.login(user, data['password'])
    if error: 
        return response_error(error)
    return response200(result)

def generate_password():
    length=8
    lowercase_characters = string.ascii_lowercase
    uppercase_characters = string.ascii_uppercase
    digits = string.digits
    special_characters = "!@#$%^&*()_+[]{}|;:,.<>?/="
    all_characters = lowercase_characters + uppercase_characters + digits + special_characters
    password = random.choice(lowercase_characters) + \
               random.choice(uppercase_characters) + \
               random.choice(digits) + \
               random.choice(special_characters) + \
               ''.join(random.choice(all_characters) for _ in range(length - 4))
               
    password_list = list(password)
    random.shuffle(password_list)
    password = ''.join(password_list)
    return password

@bp.route("/linkedin-signin", methods=["POST"])
@swag_from(f'''{document_path}/linkedin_singin.yml''')
def linkedin_login():
    data = request.json
    if 'access_token' not in data:
        return jsonify({'message': 'Access token not provided'}), 400

    access_token = data['access_token']
    api_endpoint = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
    headers = {
            'Authorization': f'Bearer {access_token}',
        }
    try:
        response = requests.get(api_endpoint, headers=headers)
        if response.status_code == 200:
            linkedin_data = response.json()
            email = linkedin_data.get("elements")[0].get("handle~").get("emailAddress")
            if email:
                result=None
                user = db.session.query(User).filter(User.email == email).first()
                if not user:
                    new_user = {
                        'email': email,
                        'password': generate_password(),
                    }
                    user_data, err = auth.create_user(new_user)
                    if err: return err and response_error(err)
                    result = user_data
                
                if not result:    
                    result = user.serialize()
                    result['access_token'] = encode_access_token(user.user_id)
                return response200(result)
            else:
                return jsonify({'message': 'Email not found in LinkedIn data'}, linkedin_data), 400
            
        else:
            return jsonify({'message': 'LinkedIn API request failed'}), 400

    except ApplicationError as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/google-signin', methods=['POST'])
@swag_from(f'''{document_path}/google_singin.yml''')
def receive_user_data():
    data = request.json
    if 'id_token' not in data:
        return jsonify({'message': 'ID token not provided'}), 400

    id_token_jwt = data['id_token']
    client_id = os.environ.get('GOOGLE_CLIENT_ID')

    try:
        decoded_token = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), client_id)
        email = decoded_token['email']
        first_name = decoded_token['given_name']
        sur_name = decoded_token['family_name']
        user: User = db.session.query(User).filter(User.email==email).first()
        result=None
        if user:
            user.first_name = first_name
            user.sur_name = sur_name
            db.session.commit()
        else:
            new_user = {
                        'email': email,
                        'first_name': first_name,
                        'sur_name': sur_name,
                        'password': generate_password()
                    }
            user_data, err = auth.create_user(new_user)
            if err: return err and response_error(err)
            result = user_data

        if not result:    
            result = user.serialize()
            result['access_token'] = encode_access_token(user.user_id)
        return response200(result)
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'ID token has expired'}), 400
    except jwt.DecodeError:
        return jsonify({'message': 'Invalid ID token'}), 400

@bp.route("/me", methods=["GET"])
@authorized()
@swag_from(f'''{document_path}/me.yml''')
def get_current_user():
    user = db.session.query(User).get(request.user_id)
    if not user:
        return response_error(ERROR_CODE['USER_NOT_FOUND'])
    return response200(user.serialize())

UPDATE_USER_INFO = Schema({
    Optional('phone_number'): All(str, Length(max=15)),
    Optional('country'): str,
    Optional('password'): str,
    Optional('new_password'): str,
    Optional('avatar_id'): validators.Coerce(uuid.UUID),
    Optional('first_name'): str,
    Optional('sur_name'): str,
})

@bp.route("/me", methods=["PATCH"])
@authorized()
@swag_from(f'''{document_path}/update_user_info.yml''')
def update_user_info():
    user_id = request.user_id
    data = UPDATE_USER_INFO(request.json)
    user = db.session.query(User).get(user_id)
    if not user:
        return response_error(ERROR_CODE['USER_NOT_FOUND'])

    # check if avatar is existed
    # if 'avatar_id' in data:
    #     existed_avatar = db.session.query(FileUpload).get(data['avatar_id'])
    #     if not existed_avatar:
    #         return response_error(ERROR_CODE['FILE_UPLOAD_NOT_FOUND'])
    # check if change password must send old password
    if 'new_password' in data:
        if not 'password' in data:
            return response_error(ERROR_CODE['OLD_PASSWORD_NOT_EXIST'])
        if not user.check_password(data['password']):               
            return response_error(ERROR_CODE['PASSWORD_IS_INVALID'])

    result = auth.update_user_info(user, data)
    return response200(result)

USER_FORGOT_PASSWORD_EMAIL = Schema({
    Required('email'): All(str, Lower),
})
@bp.route("/forgot-password", methods=["POST"])
@swag_from(f'''{document_path}/forgot_password.yml''')
def forgot_password():
    data = USER_FORGOT_PASSWORD_EMAIL(request.json)
      
    data, err = auth.forgot_password(data)
    return err and response_error(err) or response200(data)

USER_RESET_PASSWORD_EMAIL = Schema({
    Required('token'): str,
    Required('password'): str,
})
@bp.route("/reset-password", methods=["POST"])
@swag_from(f'''{document_path}/reset_password.yml''')
def reset_password():
    data = USER_RESET_PASSWORD_EMAIL(request.json)
            
    data, err = auth.reset_password(data)
    return err and response_error(err) or response200(data)
