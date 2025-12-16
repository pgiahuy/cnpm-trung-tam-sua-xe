import math
from datetime import date, timedelta

import cloudinary
import cloudinary.uploader
from flask import render_template, request, session, url_for, flash, jsonify, abort
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message
from werkzeug.utils import redirect

import dao
from garage import app, login, db, utils, mail
from garage.decorators import anonymous_required
from garage.models import UserRole, AppointmentStatus


@app.route("/")
def index():
    items = dao.load_menu_items()
    services = dao.load_services()
    spare_parts = dao.load_spare_parts()
    return render_template('index.html', items=items, services=services, spare_parts=spare_parts)


@app.context_processor
def common_adtributes():
    return {
        "items": dao.load_menu_items(),
        "stats_cart": utils.count_cart(session.get('cart'))

    }


@app.route("/register", methods=['GET', 'POST'])
def register():
    err_msg = None
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password == confirm:
            username = request.form.get('username')
            avatar = request.files.get('avatar')
            file_path = None
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            if avatar:
                upload_result = cloudinary.uploader.upload(avatar)
                file_path = upload_result["secure_url"]
            try:
                dao.add_user(username=username, password=password, avatar=file_path, full_name=full_name, phone=phone)
                return render_template("register.html", success=True)
            except:
                db.session.rollback()
                err_msg = "Hệ thống đang lỗi!"
        else:
            err_msg = "Mật khẩu không khớp!"

    return render_template('register.html', err_msg=err_msg)


@app.route("/login", methods=['get', 'post'])
@anonymous_required
def login_my_user():
    err_msg = None
    next_page = request.args.get('next') or request.form.get('next')
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username, password)

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
            err_msg = "Username hoac password khong dung!!!"

    return render_template('login.html', err_msg=err_msg)


@app.route('/admin-login', methods=['post'])
def admin_login_process():
    pass


@app.route("/logout")
def logout_my_user():
    session.pop('cart', None)
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

        if request.form.get("scheduleTime"):
            form_data['scheduleTime'] = request.form.get("scheduleTime")

            vehicle_type = form_data['vehicleType']
            license_plate = form_data['licensePlate']
            description = form_data['description']
            time_slot = form_data['scheduleTime']

            if not vehicle_type or not license_plate:
                flash("Vui lòng nhập đầy đủ loại xe và biển số!", "warning")
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
                    flash(
                        "Biển số xe không hợp lệ. VD: 59X2-123.45 (xe máy), 30A-123.45 (ô tô)",
                        "danger"
                    )

    time_slots = dao.get_time_slots_for_date(selected_date)

    return render_template(
        "bookrepair.html",
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
    user = current_user

    if not customer:
        flash("Không tìm thấy thông tin khách hàng!", "danger")
        return redirect(url_for("user_profile"))

    if request.method == "POST":
        has_changed = False

        full_name = request.form.get("full_name")
        if (customer.full_name or "") != (full_name or ""):
            customer.full_name = full_name
            has_changed = True

        phone = request.form.get("phone")
        if (customer.phone or "") != (phone or ""):
            customer.phone = phone
            has_changed = True

        address = request.form.get("address")
        if (customer.address or "") != (address or ""):
            customer.address = address
            has_changed = True

        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            upload_result = cloudinary.uploader.upload(avatar_file)
            new_avatar = upload_result["secure_url"]

            if user.avatar != new_avatar:
                user.avatar = new_avatar
                has_changed = True

        if not has_changed:
            flash("Không có thay đổi nào để cập nhật.", "warning")
            return redirect(url_for("user_edit_profile"))

        try:
            db.session.commit()
            flash("Cập nhật hồ sơ thành công!", "success")
            return redirect(url_for("user_profile"))
        except Exception as ex:
            db.session.rollback()
            flash("Có lỗi xảy ra khi cập nhật!", "danger")
            print(ex)

    return render_template(
        "user/edit-profile.html",
        customer=customer,
        user=user
    )


@app.route("/user/appointments")
@login_required
def user_appointment_history():
    appointments = dao.get_appointments_by_user(current_user.id)
    return render_template("user/appointments-history.html", appointments=appointments)


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

        old_hash = dao.md5_hash(old_password)
        new_hash = dao.md5_hash(new_password)

        if old_hash != current_user.password:
            flash("Mật khẩu hiện tại không đúng!", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("Mật khẩu mới không khớp!", "warning")
            return redirect(url_for("change_password"))

        if new_hash == current_user.password:
            flash("Mật khẩu mới không được trùng với mật khẩu cũ!", "warning")
            return redirect(url_for("change_password"))

        current_user.password = new_hash
        db.session.commit()

        flash("Đổi mật khẩu thành công!", "success")
        return redirect(url_for("user_profile"))

    return render_template("user/change-password.html")


@app.route("/api/carts", methods=['post'])
def add_to_cart():
    cart = session.get('cart')

    if not cart:
        cart = {}

    id = str(request.json.get('id'))

    if id in cart:
        cart[id]["quantity"] += 1
    else:
        cart[id] = {
            "id": id,
            "name": request.json.get('name'),
            "unit_price": request.json.get('unit_price'),
            "quantity": 1
        }

    session['cart'] = cart

    print(session['cart'])

    return jsonify(utils.count_cart(cart=cart))


@app.route('/cart')
def cart():
    return render_template("cart.html")


@app.route('/api/update-cart', methods=['put'])
def update_cart():
    data = request.json
    id = str(data.get('id'))
    quantity = data.get('quantity')

    cart = session.get('cart')

    if cart and id in cart:
        cart[id]['quantity'] = quantity
        session['cart'] = cart

    return jsonify(utils.count_cart(cart=cart))


@app.route('/api/delete-cart/<product_id>', methods=['delete'])
def delete_cart(product_id):
    cart = session.get('cart')

    if cart and product_id in cart:
        del cart[product_id]
        session['cart'] = cart

    return jsonify(utils.count_cart(cart=cart))


# Thanh toán
@app.route('/api/pay', methods=['POST'])
@login_required
def pay():
    try:
        utils.add_receipt(session.get('cart'))
        session.pop('cart', None)
        return jsonify({'code': 200})
    except Exception as e:
        print(e)
        return jsonify({'code': 400})


# Xong thanh toán

@app.route("/user/appointments/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    appointment = dao.get_appointment_by_id(appointment_id)

    if not appointment or appointment.customer.user_id != current_user.id:
        flash("Không tìm thấy lịch hẹn!", "danger")
        return redirect(url_for("user_appointment_history"))

    if appointment.status != AppointmentStatus.BOOKED:
        flash("Không thể hủy lịch này!", "warning")
        return redirect(url_for("user_appointment_history"))

    dao.cancel_appointment(appointment)

    flash("Hủy lịch hẹn thành công!", "success")
    return redirect(url_for("user_appointment_history"))


@app.route("/user/appointments/<int:appointment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_appointment(appointment_id):
    appointment = dao.get_appointment_by_id(appointment_id)

    if not appointment or appointment.customer.user_id != current_user.id:
        flash("Không tìm thấy lịch hẹn!", "danger")
        return redirect(url_for("user_appointment_history"))

    if appointment.status != AppointmentStatus.BOOKED:
        flash("Không thể chỉnh sửa lịch này!", "warning")
        return redirect(url_for("user_appointment_history"))

    selected_date = appointment.schedule_time.date()
    current_slot = appointment.schedule_time.strftime("%H:%M") + " - " + (
            appointment.schedule_time + timedelta(hours=1)
    ).strftime("%H:%M")

    time_slots = dao.get_time_slots_for_date(selected_date)

    if request.method == "POST":
        action = request.form.get("action_type")

        if action == "update_slots":
            selected_date = date.fromisoformat(request.form.get("scheduleDate"))
            time_slots = dao.get_time_slots_for_date(selected_date)

        elif action == "save":
            selected_date = date.fromisoformat(request.form.get("scheduleDate"))
            time_slot = request.form.get("scheduleTime")
            note = request.form.get("description")

            new_schedule_time = dao.parse_time_slot(time_slot, selected_date)

            has_changed = False

            if appointment.schedule_time != new_schedule_time:
                appointment.schedule_time = new_schedule_time
                has_changed = True

            if (appointment.note or "") != (note or ""):
                appointment.note = note
                has_changed = True

            if not has_changed:
                flash("Không có thay đổi nào để cập nhật.", "warning")
                return redirect(url_for(
                    "edit_appointment",
                    appointment_id=appointment.id
                ))

            db.session.commit()
            flash("Cập nhật lịch hẹn thành công!", "success")
            return redirect(url_for("user_appointment_history"))

    return render_template(
        "user/edit-appointment.html",
        appointment=appointment,
        selected_date=selected_date,
        time_slots=time_slots,
        current_slot=current_slot
    )


@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    message = request.form.get('message')

    admin_content = f"""
NEW CONSULTATION REQUEST

A customer has just submitted a consultation request via the Garage website.

Cusomer's information:
* Full name      : {name}
* Phone number   : {phone}
* Email address  : {email or 'Không cung cấp'}

CONTENT:
{message or 'Không có nội dung'}


SENT AT:
{date.today().strftime('%d/%m/%Y')}

Cre: Website Garage24h
"""

    admin_msg = Message(
        subject="[Garage] New Request From Customer",
        recipients=["nguyenlyminuong1234567890@gmail.com"],
        body=admin_content
    )

    mail.send(admin_msg)

    if email:
        customer_content = f"""
Chào {name},

Garage đã nhận được yêu cầu tư vấn của bạn.

Nhân viên Garage sẽ liên hệ với bạn trong thời gian sớm nhất
qua số điện thoại {phone}.

Cảm ơn bạn đã tin tưởng dịch vụ của chúng tôi!

---
Garage24h – Chăm sóc xe chuyên nghiệp 24/7
"""

        customer_msg = Message(
            subject="[EMAIL PHẢN HỒI] Garage24h đã nhận được yêu cầu tư vấn của bạn",
            recipients=[email],
            body=customer_content
        )

        mail.send(customer_msg)

    flash("Gửi yêu cầu tư vấn thành công! Chúng tôi sẽ liên hệ sớm.", "success")
    return redirect('/')


@app.route("/sparepart/<int:id>")
def sparepart_detail(id):
    sparepart = dao.get_sparepart_by_id(id)
    if not sparepart:
        abort(404)

    return render_template("sparepart-detail.html", sparepart=sparepart)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
