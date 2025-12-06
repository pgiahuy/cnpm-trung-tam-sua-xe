from garage import db, bcrypt
from garage.models import User


def add_user(name, username, password, avatar=None):
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(name=name, username=username, password=hashed, avatar=avatar)
    db.session.add(user)
    db.session.commit()
    return user
