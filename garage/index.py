import math
from datetime import date

import cloudinary
import cloudinary.uploader
from flask import render_template, request, session, jsonify, url_for, flash
from flask_admin import Admin
from werkzeug.utils import redirect
from flask_login import current_user,login_user,logout_user, login_required
from garage import app, login, admin, db
import dao
from garage.decorators import anonymous_required
from garage.models import UserRole
from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash

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
    next_page = request.args.get('next') or request.form.get('next')
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user =  dao.auth_user(username, password)

        if user:
            login_user(user)
            print(current_user.role)
            if next_page:
                return redirect(next_page)
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
    page = request.args.get('page', 1, type=int)
    services = dao.load_services(page=page)
    page_of_services = math.ceil(dao.count_services() / app.config["PAGE_SIZE"])
    return render_template('services.html', services=services, page_of_services=page_of_services, page=page)


@login.unauthorized_handler
def unauthorized_callback():
    flash("Bạn cần đăng nhập để tiếp tục!", "warning")
    return redirect('/login?next=' + request.path)

@app.route("/bookrepair", methods=["GET", "POST"])
@login_required
def booking():
    err_msg = None
    selected_date = date.today()

    form_data = {
        'vehicleType': request.form.get("vehicleType", ''),
        'licensePlate': request.form.get("licensePlate", ''),
        'description': request.form.get("description", ''),
        'scheduleTime': '',
    }

    if request.method == "POST":
        if "scheduleDate" in request.form:
            try:
                selected_date = date.fromisoformat(request.form["scheduleDate"])
            except ValueError:
                pass

        if "scheduleTime" in request.form and request.form.get("scheduleTime"):

            form_data['scheduleTime'] = request.form.get("scheduleTime")

            vehicle_type = form_data['vehicleType']
            license_plate = form_data['licensePlate']
            description = form_data['description']
            time_slot = form_data['scheduleTime']

            if not vehicle_type or not license_plate:
                err_msg = "Vui lòng nhập đầy đủ thông tin loại xe và biển số."
            else:
                ok = dao.add_appointment(
                    vehicle_type=vehicle_type,
                    license_plate=license_plate,
                    description=description,
                    time_slot=time_slot,
                    selected_date=selected_date
                )

                if ok:
                    return redirect(url_for("index"))
                else:
                    err_msg = "Đặt lịch thất bại. Vui lòng thử lại!"

    time_slots = dao.get_time_slots_for_date(selected_date)

    return render_template(
        "bookrepair.html",
        err_msg=err_msg,
        selected_date=selected_date,
        time_slots=time_slots,
        form_data=form_data
    )


@app.route("/services/<int:service_id>")
def site_service_detail(service_id):
    service = dao.get_service_by_id(service_id)
    if service:
        return render_template('detail-services.html', service=service)
    else:
        return "Không tìm thấy dịch vụ."

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/user/profile")
@login_required
def user_profile():
    return render_template("user/profile.html", user=current_user)

@app.route("/user/profile/edit", methods=["GET", "POST"])
@login_required
def user_edit_profile():
    customer = dao.get_customer_by_user_id(current_user.id)
    user = current_user  # avatar nằm ở user

    if not customer:
        flash("Không tìm thấy thông tin khách hàng!", "danger")
        return redirect(url_for("user_profile"))

    if request.method == "POST":

        customer.full_name = request.form.get("full_name")
        customer.phone = request.form.get("phone")
        customer.address = request.form.get("address")

        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            upload_result = cloudinary.uploader.upload(avatar_file)
            user.avatar = upload_result["secure_url"]

        try:
            db.session.commit()
            flash("Cập nhật hồ sơ thành công!", "success")
            return redirect(url_for("user_profile"))
        except Exception as ex:
            db.session.rollback()
            flash("Có lỗi xảy ra khi cập nhật!", "danger")
            print(ex)

    return render_template("user/edit-profile.html", customer=customer, user=user)

@app.route("/user/appointments")
@login_required
def user_appointment_history():
    appointments = dao.get_appointments_by_user(current_user.id)
    return render_template("user/appointments-history.html",appointments=appointments)


@app.errorhandler(403)
def forbidden_error(e):
    return render_template('errors/403.html'), 403



@app.route("/sparepart")
def site_spareparts():
    page = request.args.get('page', 1, type=int)

    spare_parts = dao.load_sparepart(page=page)

    page_of_spareparts = math.ceil(
        dao.count_sparepart() / app.config["PAGE_SIZE"]
    )

    return render_template(
        "sparepart.html",
        spare_parts=spare_parts,
        page_of_spareparts=page_of_spareparts,
        page=page
    )


@app.route("/user/vehicles")
@login_required
def user_vehicles():
    vehicles = dao.index_vehicles_by_user(current_user.id)
    return render_template("user/vehicles.html", vehicles=vehicles)

@app.route("/user/orders")
@login_required
def user_orders_history():
    receipts = dao.index_receipts_by_user(current_user.id)
    return render_template("user/orders.html", receipts=receipts)
@app.route("/user/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # 1. Kiểm tra mật khẩu cũ
        if not check_password_hash(current_user.password, old_password):
            flash("Mật khẩu hiện tại không đúng!", "danger")
            return redirect(url_for("change_password"))

        # 2. Kiểm tra mật khẩu mới
        if new_password != confirm_password:
            flash("Mật khẩu mới không khớp!", "warning")
            return redirect(url_for("change_password"))

        # 3. Lưu mật khẩu mới (HASH)
        current_user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Đổi mật khẩu thành công!", "success")
        return redirect(url_for("user_profile"))

    return render_template("user/change-password.html")

if __name__ == "__main__":
    app.run(debug=True,port=5000)

