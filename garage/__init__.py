from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
bcrypt = Bcrypt()
app = Flask(__name__)

app.secret_key = "dwdswdw"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/garage?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] =3
bcrypt.init_app(app)
db=SQLAlchemy(app)
# login = LoginManager(app)