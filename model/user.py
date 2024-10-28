import random, string
from datetime import datetime
from model.db import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum, unique
from util.hash_util import check_password, hash_password
import pycountry
import uuid
from sqlalchemy.dialects.postgresql import ARRAY
# from model.instructor import Instructor



class Skill(db.Model):
    __tablename__ = "skill"

    # Column
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)

    def serialize(self):
        return self.name


class UserSkill(db.Model):
    __tablename__ = "user_skill"

    # Column
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"))
    skill_id = db.Column(UUID(as_uuid=True), db.ForeignKey("skill.id"))


class UserType(Enum):
    normal_user = 0
    verified_educator = 1
    organization = 2

    @classmethod
    def list(cls):
        return [t.value for t in cls]
    
class UserRole(Enum):
    learner = "learner"
    mentor = "mentor"
    educator = "educator"


class User(db.Model):
    __tablename__ = "user"
    __json_hidden__ = ["password"]
    __update_field__ = []
    __filter_field__ = []

    # Column
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.VARCHAR(255), nullable=False, unique=True)
    _password = db.Column(db.Text, nullable=False)
    forgot_password_key = db.Column(db.VARCHAR(255))
    first_name = db.Column(db.String(255))
    sur_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(15))
    # avatar_id = db.Column(UUID(as_uuid=True), db.ForeignKey("file_upload.file_id"))
    gender = db.Column(db.String(1), default="m")
    current_position = db.Column(db.String(255))
    key_position = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    description = db.Column(db.Text)
    work_place = db.Column(db.String(255))
    user_type = db.Column(
        db.Integer, default=0
    )  # 0: normal-user; 1: verified-educator, 2: organization
    role = db.Column(db.Enum(UserRole),
                       default = UserRole.learner,
                       server_default="learner",
                       nullable = False)
    level = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    country = db.Column(db.String(3), default="VNM")  # comment='ISO 3166-1 alpha-3'
    skill = db.Column(ARRAY(db.String(255)), default=[])
    otp = db.Column(db.String(6), unique=True)
    otp_date = db.Column(db.DateTime)
    slug = db.Column(db.String(255), unique=True)

     # Thiết lập quan hệ 1-N với Book
    books = relationship("Book", back_populates="author")

    # Thiết lập quan hệ N-N với Receipt
    receipts = relationship("Receipt", back_populates="user")

    def serialize(self):
        country_name = ""
        if self.country:
            country = pycountry.countries.get(alpha_3=self.country)
            country_name = country.name if country else ""

        data = {
            "user_id": self.user_id,
            "role": self.role,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "sur_name": self.sur_name,
            "phone_number": self.phone_number,
            # "avatar": self.avatar.serialize() if self.avatar else None,
            "user_type": self.user_type,
            "gender": self.gender,
            "current_position": self.current_position,
            "key_position": self.key_position,
            "date_of_birth": str(self.date_of_birth),
            "description": self.description,
            "work_place": self.work_place,
            "country": country_name,
            "skills": self.skill,
            "otp": self.otp,
            "otp_date": self.otp_date,
            "slug": self.slug,
            # "is_filled_educator_profile": self.educator_profile is not None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        # if self.user_type == UserType.verified_educator.value:
        #     if not self.instructor:
        #         self.instructor = Instructor(user_id=self.user_id, teaching_hours=50)
        #         db.session.add(self.instructor)
        #         db.session.commit()

        #     data["teaching_hours"] = self.instructor.teaching_hours
        #     data["teaching_courses_count"] = (
        #         len(self.teaching_courses) if self.teaching_courses else 0
        #     )

        return data

    def simplified_serialize(self):
        data = {
            "id": self.user_id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "sur_name": self.sur_name,
            "phone_number": self.phone_number,
            # "avatar": self.avatar.serialize() if self.avatar else None,
            "current_position": self.current_position,
            "key_position": self.key_position,
            "work_place": self.work_place,
            "description": self.description,
            "skills": self.skill,
            "slug": self.slug,
        }

        # if self.user_type == UserType.verified_educator.value:
        #     if not self.instructor:
        #         self.instructor = Instructor(user_id=self.user_id, teaching_hours=50)
        #         db.session.add(self.instructor)
        #         db.session.commit()

        #     data["teaching_hours"] = self.instructor.teaching_hours
        #     data["teaching_courses_count"] = (
        #         len(self.teaching_courses) if self.teaching_courses else 0
        #     )

        return data

    def list_serialize(self):
        data = {
            "id": self.user_id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "sur_name": self.sur_name,
            "phone_number": self.phone_number,
            # "avatar": self.avatar.serialize() if self.avatar else None,
            "key_position": self.key_position,
            "slug": self.slug,
        }

        return data

    @hybrid_property
    def password(self):
        return None

    @password.setter
    def password(self, value):
        self._password = hash_password(value)

    def check_password(self, password):
        return check_password(self._password, password)

    def generate_forgot_password(self):
        self.forgot_password_code = "".join(
            [random.choice(string.ascii_letters) for n in range(5)]
        ).upper()

# class UserFollower(db.Model):
#     __tablename__ = "user_follower"

#     # Column
#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"))
#     follower_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.user_id"))
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(
#         db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
#     )

#     followee = relationship("User", foreign_keys=[user_id])
#     follower = relationship("User", foreign_keys=[follower_id])

#     def serialize(self):
#         return {
#             "id": self.id,
#             "followee": self.followee.simplified_serialize(),
#         }
