from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)

app.secret_key = "dwdswdw"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/garage?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3
app.config["VAT_RATE"] = 0.1
#==============================

cloudinary.config(  cloud_name='dslzjm9y1',
                    api_key='378681865892523',
                    api_secret='JoV-kP2mQAXaW3dfDlQAuuqP7pA')

db=SQLAlchemy(app)
login = LoginManager(app)

