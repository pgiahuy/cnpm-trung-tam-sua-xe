
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, PrimaryKeyConstraint
from enum import Enum as RoleEnum
from garage import db, app
from datetime import datetime


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime,default= datetime.now())

    def __str__(self):
        return self.name

class User(Base,UserMixin):
    username = Column(String(150), nullable=False ,unique=True)
    password = Column(String(150), nullable = False)
    avatar = Column(String(300), default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png")
    user_role = Column(Enum(UserRole), default= UserRole.USER)

if __name__=="__main__":
    with app.app_context():
        db.create_all()