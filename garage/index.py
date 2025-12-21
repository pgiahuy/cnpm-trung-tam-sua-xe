import json
import math
import time
from datetime import date, timedelta, datetime
import re

import cloudinary
import cloudinary.uploader
from flask import render_template, request, session, url_for, flash, jsonify, abort, current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import redirect

import dao
from garage import app, login, db, utils, mail
from garage.decorators import anonymous_required
from garage.models import UserRole, AppointmentStatus, Service, SparePart, PaymentStatus, Receipt, Payment, ReceiptItem, \
    RepairForm, SystemConfig, Vehicle, Customer, User, VehicleStatus, RepairStatus, ReceiptItemType
from garage.vnpay import build_vnpay_url


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
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        avatar = request.files.get('avatar')

        # 1. Validate SĐT VN
        if not re.match(r'^(0)(3|5|7|8|9)\d{8}$', phone):
            err_msg = "Số điện thoại không hợp lệ, phải gồm 10 kí tự. VD: 0123456789"
            return render_template('register.html', err_msg=err_msg)

        # 2. Check trùng
        if dao.is_username_exists(username):
            err_msg = "Tên đăng nhập đã tồn tại"
            return render_template('register.html', err_msg=err_msg)

        if dao.is_phone_exists(phone):
            err_msg = "Số điện thoại đã được sử dụng"
            return render_template('register.html', err_msg=err_msg)

        # 3. Validate mật khẩu
        if len(password) < 8:
            err_msg = "Mật khẩu phải có ít nhất 8 ký tự"
            return render_template('register.html', err_msg=err_msg)

        if not re.search(r'[A-Z]', password) or not re.search(r'\d', password):
            err_msg = "Mật khẩu phải có chữ hoa và số"
            return render_template('register.html', err_msg=err_msg)

        if password != confirm:
            err_msg = "Mật khẩu không khớp!"
            return render_template('register.html', err_msg=err_msg)

        # 4. Upload avatar
        file_path = None
        if avatar:
            upload_result = cloudinary.uploader.upload(avatar)
            file_path = upload_result["secure_url"]

        try:
            email = request.form.get('email')  # có thể rỗng

            dao.add_user(
                username=username,
                password=password,
                avatar=file_path,
                full_name=full_name,
                phone=phone,
                email=email  # truyền thêm email
            )
            return render_template("register.html", success=True)
        except Exception as ex:
            db.session.rollback()
            err_msg = "Hệ thống đang lỗi!"
            print(ex)



    return render_template('register.html', err_msg=err_msg)

@app.route("/login", methods=['GET', 'POST'])
@anonymous_required
def login_my_user():
    err_msg = None
    next_page = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username, password)

        if user:
            login_user(user)

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
                        "Biển số xe không hợp lệ. VD: 59A1-12345 hoặc 59AA-1234 (xe máy), 30A-12345 hoặc 59AA-1234 (ô tô, xe tải)",
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
    page_of_spareparts = math.ceil(dao.count_sparepart() / app.config["PAGE_SIZE"])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Nếu là AJAX → chỉ render phần list
        return render_template('sparepart_list.html',
                               spare_parts=spare_parts,
                               page=page,
                               page_of_spareparts=page_of_spareparts)

    # Bình thường → render full page
    return render_template("sparepart.html",
                           spare_parts=spare_parts,
                           page=page,
                           page_of_spareparts=page_of_spareparts)


@app.route("/user/vehicles")
@login_required
def user_vehicles():
    vehicles = dao.index_vehicles_by_user(current_user.id)

    return render_template("user/vehicles.html", vehicles=vehicles)

@app.route('/vehicles/<int:customer_id>')
def get_vehicles_by_customer(customer_id):
    if customer_id == 0 or customer_id == '' or customer_id is None:
        return jsonify([])

    vehicles = Vehicle.query.filter_by(customer_id=customer_id, active=True).all()
    return jsonify([
        {
            'id': v.id,
            'license_plate': v.license_plate,
            'vehicle_type': v.vehicle_type
        } for v in vehicles
    ])

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

@app.route('/receipt/<int:receipt_id>')
def receipt_detail(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    return render_template('user/receipt_detail.html', receipt=receipt)





@app.route('/api/pay_spare_part', methods=['POST'])
@login_required
def pay():
    cart = session.get('cart')
    if not cart:
        return jsonify({'code': 400, 'msg': 'Cart rỗng'})
    txn_ref = f"{current_user.id}_{int(time.time())}"

    vat_rate = 0 #dao.get_vat_value()

    total = utils.count_cart(cart)['total_amount']
    total += vat_rate*total

    payment = Payment(
        user_id=current_user.id,
        amount=total,
        vat_rate=vat_rate,
        method='VNPAY',
        type='BUY',
        transaction_ref=txn_ref,
        status=PaymentStatus.PENDING,
        cart_snapshot=json.dumps(cart)
    )
    db.session.add(payment)
    db.session.commit()

    pay_url = build_vnpay_url(total, txn_ref)

    return jsonify({
        'code': 200,
        'pay_url': pay_url
    })


@app.route('/api/pay_repair/<int:repair_id>', methods=['POST'])
@login_required
def pay_repair(repair_id):
    repair = RepairForm.query.get_or_404(repair_id)
    total_before_vat = repair.total_before_vat

    vat_rate = dao.get_vat_value()

    total_amount = total_before_vat + total_before_vat * vat_rate

    txn_ref = f"{repair.id}_{int(time.time())}"

    payment = Payment(
        user_id=current_user.id,
        repair_id=repair.id,
        amount=total_amount,
        vat_rate=vat_rate,
        method="VNPAY",
        type="REPAIR",
        status=PaymentStatus.PENDING,
        transaction_ref=txn_ref
    )
    db.session.add(payment)
    db.session.commit()

    pay_url = build_vnpay_url(total_amount, txn_ref)
    return jsonify({'code': 200, 'pay_url': pay_url})




@app.route('/billing/vnpay_return')
def vnpay_return():
    response_code = request.args.get('vnp_ResponseCode')
    txn_ref = request.args.get('vnp_TxnRef')
    vnp_trans_no = request.args.get('vnp_TransactionNo')

    payment = Payment.query.filter_by(
        transaction_ref=txn_ref,
        method='VNPAY'
    ).first()

    if not payment:
        return "Payment không tồn tại", 404

    if response_code != '00':
        payment.status = PaymentStatus.FAILED
        db.session.commit()
        return render_template("payment_failed.html")

    # Thanh toán thành công
    payment.status = PaymentStatus.SUCCESS
    payment.vnp_transaction_no = vnp_trans_no
    type = getattr(payment, 'type')
    subtotal = payment.amount/(1+payment.vat_rate)
    receipt = Receipt(
        customer_id=payment.user.customer.id,
        subtotal=subtotal,
        vat_rate=payment.vat_rate,
        total_paid=payment.amount,
        payment_method="VNPAY",
        type=type  # BUY hoặc REPAIR
    )
    db.session.add(receipt)
    db.session.flush()  # để có receipt.id


    # Tạo receipt item
    if type == "BUY":

        cart = json.loads(payment.cart_snapshot)

        if not cart:
            return jsonify({'code': 400, 'msg': 'Cart rỗng'})

        for c in cart.values():
            item = ReceiptItem(
                receipt_id=receipt.id,
                spare_part_id=int(c['id']),
                quantity=c['quantity'],
                unit_price=c['unit_price'],
                total_price=c['quantity'] * c['unit_price']
            )
            db.session.add(item)
        session.pop('cart', None)





    elif type == "REPAIR":
        repair = payment.repair
        for d in repair.details:

            if d.service_price and d.service_price > 0:
                db.session.add(ReceiptItem(
                    receipt_id=receipt.id,
                    repair_detail_id=d.id,
                    item_type=ReceiptItemType.SERVICE,
                    service_id=d.service_id,
                    quantity=1,
                    unit_price=d.service_price,
                    total_price=d.service_price
                ))

            if d.spare_part_id and d.spare_part_price:
                db.session.add(ReceiptItem(
                    receipt_id=receipt.id,
                    repair_detail_id=d.id,
                    item_type=ReceiptItemType.SPARE_PART,
                    spare_part_id=d.spare_part_id,
                    quantity=d.quantity,
                    unit_price=d.spare_part_price,
                    total_price=d.quantity * d.spare_part_price
                ))
        repair.repair_status = RepairStatus.PAID
        repair.vehicle.vehicle_status = VehicleStatus.DELIVERED


    payment.receipt_id = receipt.id
    db.session.commit()

    return render_template("payment_success.html", receipt=receipt)


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

    page = request.args.get('page', 1, type=int)
    comments = utils.get_comments(sparepart_id=id, page=page)
    pagination = utils.get_comment_pagination(sparepart_id=id, current_page=page)

    return render_template(
        "sparepart-detail.html",
        sparepart=sparepart,
        comments=comments,
        pagination=pagination,
        current_page=page
    )


@app.route('/flash-login-required', methods=['POST'])
def flash_login_required():
    next_url = request.referrer or '/'
    flash(f'Bạn cần <a href="/login?next={next_url}" class="text-warning fw-bold">đăng nhập</a> để tiếp tục', 'warning')
    return '', 204


@app.route("/search")
def search():
    kw = request.args.get("kw", "").strip()
    scope = request.args.get("scope", "all")  # all, service, sparepart

    services = []
    spare_parts = []

    if kw:
        if scope in ["all", "service"]:
            services = Service.query.filter(Service.name.ilike(f"%{kw}%")).all()
            services = dao.unique_by_name(services)

        if scope in ["all", "sparepart"]:
            spare_parts = SparePart.query.filter(SparePart.name.ilike(f"%{kw}%")).all()
            spare_parts = dao.unique_by_name(spare_parts)

    return render_template(
        "search.html",
        kw=kw,
        services=services,
        spare_parts=spare_parts,
        scope=scope
    )


@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    try:
        data = request.get_json()
        content = data.get('content')
        sparepart_id = data.get('sparepart_id')

        if not content or not sparepart_id:
            return jsonify({'status': 400, 'err_msg': 'Thiếu dữ liệu'}), 400

        comment = utils.add_comment(content=content.strip(), sparepart_id=sparepart_id)

        return jsonify({
            'status': 201,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'username': current_user.username,
                'created_date': comment.created_date.strftime('%d/%m/%Y %H:%M')
            }
        })
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'status': 500, 'err_msg': 'Lỗi hệ thống'}), 500

@app.route('/api/check-phone')
def check_phone():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({'exists': False})

    exists = db.session.query(Customer.id).filter(
        Customer.phone == phone
    ).first() is not None

    return jsonify({'exists': exists})


@app.route('/api/check-username')
def check_username():
    username = request.args.get('username')
    if not username:
        return jsonify({'exists': False})

    exists = db.session.query(User.id).filter(
        User.username == username
    ).first() is not None

    return jsonify({'exists': exists})
# Tạo serializer để mã hóa token
s = URLSafeTimedSerializer(app.secret_key)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@anonymous_required
def reset_password(token):
    try:
        data = s.loads(token, salt='reset-password', max_age=3600)  # 1 giờ
        user_id = data['user_id']
    except:
        flash("Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.", "danger")
        return redirect(url_for('forgot_password'))

    user = User.query.get(user_id)
    if not user or user.reset_token != token or user.reset_token_expiry < datetime.utcnow():
        flash("Link không hợp lệ.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm or len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'\d', password):
            flash("Mật khẩu không hợp lệ hoặc không khớp!", "danger")
            return render_template('reset_password.html', token=token)

        user.password = dao.md5_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay.", "success")
        return redirect(url_for('login_my_user'))

    return render_template('reset_password.html', token=token)
@app.route('/forgot-password', methods=['GET', 'POST'])
@anonymous_required
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier').strip()

        # Tìm user bằng username hoặc email
        user = User.query.join(Customer).filter(
            (User.username == identifier) |
            (Customer.email == identifier)
        ).first()

        if not user or not user.customer or not user.customer.email:
            flash("Không tìm thấy tài khoản hoặc email liên kết.", "danger")
            return redirect(url_for('forgot_password'))

        # Tạo token có hạn 1 giờ
        token = s.dumps({'user_id': user.id}, salt='reset-password')

        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Link reset
        reset_url = url_for('reset_password', token=token, _external=True)

        # Gửi email
        msg = Message("Đặt lại mật khẩu - Garage Center",
                      recipients=[user.customer.email])
        msg.html = f"""
        <h3>Chào {user.customer.full_name or user.username},</h3>
        <p>Bạn đã yêu cầu đặt lại mật khẩu tài khoản Garage Center.</p>
        <p>Click vào link dưới đây để đặt lại mật khẩu (có hiệu lực trong 1 giờ):</p>
        <p><a href="{reset_url}" style="background:#ffc107;padding:10px 20px;color:black;text-decoration:none;border-radius:5px;">
            Đặt lại mật khẩu ngay
        </a></p>
        <p>Nếu bạn không yêu cầu, vui lòng bỏ qua email này.</p>
        <hr>
        <small>Garage Center - Chăm sóc xe chuyên nghiệp 24/7</small>
        """

        try:
            mail.send(msg)
            flash("Đã gửi link đặt lại mật khẩu đến email của bạn! Vui lòng kiểm tra hộp thư.", "success")
        except Exception as e:
            print(e)
            flash("Lỗi gửi email. Vui lòng thử lại sau hoặc liên hệ hotline.", "danger")

        return redirect(url_for('login_my_user'))

    return render_template('forgot_password.html')
if __name__ == "__main__":
    app.run(debug=True, port=5000)
