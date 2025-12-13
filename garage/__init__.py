from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)

app.secret_key = "dwdswdw"

#=========APP CONFIG===============
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/garage?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] =3
app.config["VAT_RATE"] = 0.1
#==============================

cloudinary.config(  cloud_name='dbxtbus46',
                    api_key='994774263527943',
                    api_secret='HLpoMPuSSuFMTLFeEP805AriVsk')

db=SQLAlchemy(app)
login = LoginManager(app)

