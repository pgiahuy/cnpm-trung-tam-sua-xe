from flask import Flask, session, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, get_locale
import cloudinary
from flask_mail import Mail

app = Flask(__name__, template_folder='templates')

app.secret_key = "dwdswdw"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/garage?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3
app.config["COMMENTS_PAGE_SIZE"] = 10
app.config["VAT_RATE"] = 0.1
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nguyenlyminuong1234567890@gmail.com'
app.config['MAIL_PASSWORD'] = 'upveulwvnwfisjdg'
app.config['MAIL_DEFAULT_SENDER'] = (
    'Garage Support',
    'nguyenlyminuong1234567890@gmail.com'
)

app.config['LANGUAGES'] = ['vi', 'en']
app.config['BABEL_DEFAULT_LOCALE'] = 'vi'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = '../translations'

babel = Babel(app)

@babel.localeselector
def select_locale():
    return session.get('lang') or 'vi'
@app.route('/change-lang/<lang>')
def change_lang(lang):
    if lang in app.config['LANGUAGES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))
@app.context_processor
def inject_lang():
    return {
        'current_lang': str(get_locale()),
        'languages': app.config['LANGUAGES']
    }

cloudinary.config(
    cloud_name='dslzjm9y1',
    api_key='378681865892523',
    api_secret='JoV-kP2mQAXaW3dfDlQAuuqP7pA'
)

db = SQLAlchemy(app)
login = LoginManager(app)
mail = Mail(app)

from garage import admin