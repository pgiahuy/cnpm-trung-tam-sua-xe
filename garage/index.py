
from flask import render_template, request, jsonify, redirect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, logout_user

from garage import app, dao, db, bcrypt
from garage.models import UserRole, User


@app.route('/')
def index():
    return render_template("index.html")

# @app.route("/register",methods=['GET','POST'])
# def register():
#     err_msg = None
#     if request.method == 'POST':
#         password = request.form.get('password')
#         confirm = request.form.get('confirm')
#         if password==confirm:
#             username = request.form.get('username')
#             name = request.form.get('name')
#             avatar = request.files.get('avatar')
#             file_path=None
#             # if avatar:
#             #     upload_result = cloudinary.uploader.upload(avatar)
#             #     file_path = upload_result["secure_url"]
#             try:
#                 dao.add_user(name=name, username=username, password=password, avatar=file_path)
#                 return redirect("/login")
#             except:
#                 db.session.rollback()
#                 err_msg = "Lỗi rồi khách ơi!"
#         else:
#             err_msg="Mật khẩu không khớp!"
#     return render_template('register.html', err_msg=err_msg)


@app.route('/login', methods=['POST'])
def login():
    err_msg = None

    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            if user.user_role == UserRole.ADMIN:

                return redirect("/admin")
            else:
                return redirect("/")
        else:
            err_msg = "Tên đăng nhập hoặc mật khẩu không đúng!"

    return render_template('login.html', err_msg=err_msg)

@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect('/login')

@app.route('/book repair')
def book_repair():


@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)

if __name__ == '__main__':
    app.run(debug=True)