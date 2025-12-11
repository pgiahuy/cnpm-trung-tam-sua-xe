import hashlib
import json

from garage import db, app
from garage.models import User, Service, SparePart


def load_services():
    return Service.query.all()

def load_spare_parts():
    return SparePart.query.all()

def load_menu_items():
    with open("data/menu_items.json", encoding="utf-8") as f:
        return json.load(f)

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






