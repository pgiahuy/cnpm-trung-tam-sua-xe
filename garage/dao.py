import hashlib
from garage import db
from garage.models import User


def add_user(name, username, password, avatar):
    password=hashlib.md5(password.encode("utf-8")).hexdigest()
    u = User(name=name,username=username,password=password,avatar=avatar)
    db.session.add(u)
    db.session.commit()

def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)
