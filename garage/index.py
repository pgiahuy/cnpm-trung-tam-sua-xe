import math
import cloudinary
import cloudinary.uploader
from flask import render_template, request, session, jsonify
from werkzeug.utils import redirect
from flask_login import current_user,login_user,logout_user
from garage import app, login, admin, db
import dao
from garage.decorators import anonymous_required
from garage.models import UserRole

@app.route("/")
def index():
    items = dao.load_menu_items()
    services = dao.load_services()
    spare_parts = dao.load_spare_parts()
    return render_template('index.html', items = items, services = services, spare_parts = spare_parts)

@app.context_processor
def common_adtributes():
    return {
        "items" : dao.load_menu_items()
    }

@app.route("/register",methods=['GET','POST'])
def register():
    err_msg=None
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password==confirm:
            username = request.form.get('username')
            avatar = request.files.get('avatar')
            file_path=None
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            if avatar:
                upload_result = cloudinary.uploader.upload(avatar)
                file_path = upload_result["secure_url"]
            try:
                dao.add_user( username=username, password=password, avatar=file_path, full_name=full_name,   phone=phone )
                return render_template("register.html", success=True)
            except:
                db.session.rollback()
                err_msg = "Hệ thống đang lỗi!"
        else:
            err_msg="Mật khẩu không khớp!"

    return render_template('register.html', err_msg=err_msg)


@app.route("/login",methods=['get','post'])
@anonymous_required
def login_my_user():
    err_msg = None

    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user =  dao.auth_user(username, password)

        if user:
            login_user(user)
            if user.role == UserRole.ADMIN:
                return redirect("/admin")
            else:
                return redirect("/")
        else:
            err_msg ="Username hoac password khong dung!!!"

    return render_template('login.html',err_msg=err_msg)

@app.route('/admin-login', methods=['post'])
def admin_login_process():
    pass

@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect('/login')

@login.user_loader
def get_user(user_id):
    return dao.get_user_by_id(user_id)

@app.route("/services")
def site_services():
    services = dao.load_services()
    return render_template('services.html', services=services)

if __name__ == "__main__":
    app.run(debug=True,port=5000)

