import hashlib
import json

from garage import db, app
from garage.models import User, Service, SparePart, Customer, UserRole


def load_services():
    return Service.query.all()

def load_spare_parts():
    return SparePart.query.all()

def load_menu_items():
    with open("data/menu_items.json", encoding="utf-8") as f:
        return json.load(f)


def add_user(username, password, avatar, full_name, phone):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = User(username=username, password=password, avatar=avatar, role=UserRole.USER)
    c = Customer(full_name=full_name, phone=phone, user=u)
    try:
        db.session.add(u)
        db.session.add(c)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        # raise ex

def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_service_by_id(service_id):
    return Service.query.get(service_id)
#
# if __name__ == '__main__':
#     with app.app_context():
#         print(get_service_by_id(1))


