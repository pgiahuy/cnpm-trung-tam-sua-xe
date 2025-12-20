import hashlib
import json

from garage import db, app
from garage.models import (User, Service, SparePart, Customer, UserRole, Vehicle, Appointment, AppointmentStatus,
                           Receipt, ReceptionForm, RepairForm, SystemConfig)
from datetime import datetime, date, time
from flask_login import current_user
import re
from flask import flash
from sqlalchemy import func

def md5_hash(password: str):
    return hashlib.md5(password.encode("utf-8")).hexdigest()

def load_services(page=None):
    query = Service.query

    if page is not None and page > 0:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        end = start + page_size
        return query.slice(start, end).all()

    return query.all()


def load_customers():
    return Customer.query.all()

def load_customer_by_id(id):
    return Customer.query.filter_by(id=id).first()

def load_confirmed_appointments():
    query = db.session.query(Appointment).filter(Appointment.status == AppointmentStatus.CONFIRMED)
    return query.all()

def load_spare_parts():
    return SparePart.query.all()

def load_menu_items():
    with open("data/menu_items.json", encoding="utf-8") as f:
        return json.load(f)


def add_user(username, password, avatar, full_name, phone):
    password = md5_hash(password)
    u = User(username=username, password=password, avatar=avatar, role=UserRole.USER)
    c = Customer(full_name=full_name, phone=phone, user=u)
    try:
        db.session.add(u)
        db.session.add(c)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        # raise ex

def auth_user(username,password):
    password = md5_hash(password)
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_appointment_by_id(appointment_id):
    return Appointment.query.get(appointment_id)

def get_service_by_id(service_id):
    return Service.query.get(service_id)

def get_customer_by_user_id(user_id):
    return Customer.query.filter_by(user_id=user_id).first()

def get_time_slots_for_date(selected_date: date):
    slots = [
        "08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00",
        "11:00 - 12:00", "13:00 - 14:00", "14:00 - 15:00",
        "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00",
        "18:00 - 19:00", "19:00 - 20:00"
    ]

    now = datetime.now()
    available = []
    today = date.today()

    if selected_date < today:
        return []

    for slot in slots:
        start_str = slot.split(" - ")[0]
        h, m = map(int, start_str.split(":"))
        slot_time = datetime.combine(selected_date, time(h, m))

        if selected_date > today or (selected_date == today and slot_time > now):
            available.append(slot)

    return available


def parse_time_slot(time_slot: str, selected_date: date):
    start_time = time_slot.split(" - ")[0]
    h, m = map(int, start_time.split(":"))
    return datetime.combine(selected_date, time(h, m))


def add_appointment(vehicle_type, license_plate, description, time_slot, selected_date):
    try:
        if not validate_license_plate(license_plate, vehicle_type):
            return False

        customer_obj = Customer.query.filter_by(user_id=current_user.id).first()
        if not customer_obj:
             raise Exception("Không tìm thấy thông tin Khách hàng liên kết với User này.")

        customer_id = customer_obj.id

        vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()

        vehicle_id = None

        if vehicle:
            vehicle_id = vehicle.id
        else:
            new_vehicle = Vehicle(
                license_plate=license_plate,
                vehicle_type=vehicle_type,
                customer_id=customer_id
            )
            db.session.add(new_vehicle)
            db.session.flush()
            vehicle_id = new_vehicle.id

        if vehicle_id is None:
            raise Exception("Không thể tạo hoặc lấy ID của Vehicle")

        appointment = Appointment(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            schedule_time=parse_time_slot(time_slot, selected_date),
            status=AppointmentStatus.BOOKED,
            note=description
        )

        db.session.add(appointment)
        db.session.commit()
        return True

    except Exception as e:
        print("DAO ERROR:", e)
        db.session.rollback()
        return False

def count_services():
    return Service.query.count()

def add_customer(full_name, phone, address, email):
    customer = Customer(
        full_name=full_name,
        phone=phone,
        address=address,
        email=email,
    )
    db.session.add(customer)
    db.session.commit()
    return customer


def add_vehicle(license_plate, vehicle_type, vehicle_status, customer_id):
    vehicle = Vehicle(
        license_plate=license_plate,
        vehicle_type=vehicle_type,
        vehicle_status=vehicle_status,
        customer_id=customer_id
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


def add_reception_form(vehicle_type, license_plate, error_description, time_slot, selected_date):
    from garage import db
    from garage.models import ReceptionForm, Vehicle

    # tìm xe theo license_plate, nếu chưa có có thể tạo mới
    vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()
    if not vehicle:
        vehicle = add_vehicle(license_plate, vehicle_type, "new", None)

    reception = ReceptionForm(
        vehicle_id=vehicle.id,
        error_description=error_description,
        time_slot=time_slot,
        date=selected_date
    )
    db.session.add(reception)
    db.session.commit()
    return reception

def get_appointments_by_user(user_id):
    customer = get_customer_by_user_id(user_id)

    if not customer:
        return []

    return (
        Appointment.query
        .filter(Appointment.customer_id == customer.id)
        .order_by(Appointment.schedule_time.desc())
        .all()
    )

def index_vehicles_by_user(user_id):
    customer = get_customer_by_user_id(user_id)
    if not customer:
        return []

    return (
        Vehicle.query
        .filter(Vehicle.customer_id == customer.id)
        .order_by(Vehicle.created_date.desc())
        .all()
    )

def index_receipts_by_user(user_id):
    customer = Customer.query.filter_by(user_id=user_id).first()

    if not customer:
        return []

    return (
        Receipt.query
        .filter(Receipt.customer_id == customer.id)
        .order_by(Receipt.paid_at.desc())
        .all()
    )


def load_sparepart(page=None):
    query = SparePart.query
    if page is not None and page > 0:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        end = start + page_size
        return query.slice(start, end).all()

    return query.all()
def count_sparepart():
    return SparePart.query.count()

def get_appointment_by_id(appointment_id):
    return Appointment.query.get(appointment_id)

def cancel_appointment(appointment: Appointment):
    appointment.status = AppointmentStatus.CANCELLED
    db.session.commit()

def update_appointment_note(appointment: Appointment, note: str):
    appointment.note = note
    db.session.commit()

CAR_PLATE_REGEX = r"^\d{2}[A-Z]-\d{5}$"
MOTOR_PLATE_REGEX = r"^\d{2}[A-Z][0-9]-\d{5}$"

def validate_license_plate(plate, vehicle_type):
    plate = plate.upper().strip()

    if vehicle_type == "car":
        return re.match(CAR_PLATE_REGEX, plate)
    elif vehicle_type == "motorbike":
        return re.match(MOTOR_PLATE_REGEX, plate)

    return False

def get_sparepart_by_id(sparepart_id):
    return SparePart.query.get(sparepart_id)

def unique_by_name(items):
    seen = set()
    unique_items = []
    for item in items:
        if item.name not in seen:
            unique_items.append(item)
            seen.add(item.name)
    return unique_items

def load_system_config(app):
    configs = SystemConfig.query.all()
    for c in configs:
        try:
            value = int(c.value)
        except:
            try:
                value = float(c.value)
            except:
                value = c.value

        app.config[c.key] = value

def get_vat_value():
    vat_obj = SystemConfig.query.filter_by(id='VAT').first()
    if vat_obj:
        try:
            return float(vat_obj.value)
        except (ValueError, TypeError):
            return 0.1
    return 0.1

def get_revenue_by_month():
    results = db.session.query(
        func.month(Receipt.paid_at).label('month'),
        func.sum(Receipt.total_paid).label('revenue')
    ).group_by(func.month(Receipt.paid_at)).all()

    return {f"Tháng {r.month}": float(r.revenue) for r in results}


def get_revenue_by_day():
    results = db.session.query(
        func.date(Receipt.paid_at).label('date'),
        func.sum(Receipt.total_paid).label('revenue')
    ).group_by(func.date(Receipt.paid_at)).all()

    return {str(r.date): float(r.revenue) for r in results}


def get_vehicle_stats():
    results = db.session.query(
        Vehicle.vehicle_type,
        func.count(ReceptionForm.id)
    ).join(Vehicle, ReceptionForm.vehicle_id == Vehicle.id) \
        .group_by(Vehicle.vehicle_type).all()
    return {r[0]: r[1] for r in results if r[0]}

def get_error_stats():
    results = db.session.query(
        ReceptionForm.error_description,
        func.count(ReceptionForm.id)
    ).group_by(ReceptionForm.error_description).limit(5).all()
    return {r[0]: r[1] for r in results}

def get_report_data(start_date_str=None, end_date_str=None, sections=None):
    report_results = {}
    today = datetime.now()

    if not start_date_str:
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = datetime.strptime(start_date_str, '%Y-%m-%d')

    if not end_date_str:
        end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        end = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    if not sections:
        sections = []

    if 'revenue_day' in sections:
        query = db.session.query(
            func.date(Receipt.paid_at).label('ngay'),
            func.sum(Receipt.total_paid).label('tong')
        ).filter(Receipt.paid_at >= start, Receipt.paid_at <= end) \
         .group_by(func.date(Receipt.paid_at)) \
         .order_by(func.date(Receipt.paid_at))

        report_results['Doanh Thu Ngay'] = [
            {'Ngày': r.ngay.strftime('%d/%m/%Y'), 'Doanh Thu (VNĐ)': float(r.tong)}
            for r in query.all()
        ]

    if 'revenue_month' in sections:
        query = db.session.query(
            func.date_format(Receipt.paid_at, '%m/%Y').label('thang'),
            func.sum(Receipt.total_paid).label('tong')
        ).filter(Receipt.paid_at >= start, Receipt.paid_at <= end) \
         .group_by('thang') \
         .order_by(func.min(Receipt.paid_at))

        report_results['Doanh Thu Thang'] = [
            {'Tháng': r.thang, 'Doanh Thu (VNĐ)': float(r.tong)}
            for r in query.all()
        ]
    vat = float(vat_obj.value)
    return vat
def is_username_exists(username):
    return db.session.query(User).filter_by(username=username).first() is not None

def is_phone_exists(phone):
    return db.session.query(Customer).filter_by(phone=phone).first() is not None
    if 'vehicle_stats' in sections:
        query = db.session.query(
            Vehicle.vehicle_type,
            func.count(ReceptionForm.id)
        ).join(Vehicle, ReceptionForm.vehicle_id == Vehicle.id) \
            .filter(ReceptionForm.created_date >= start, ReceptionForm.created_date <= end) \
            .group_by(Vehicle.vehicle_type).all()

        report_results['Thống kê lượt xe'] = [
            {
                'Loại xe': r[0] if r[0] else "Chưa xác định",
                'Số lượt đến sửa': r[1]
            } for r in query
        ]

    if 'error_stats' in sections:
        query = db.session.query(
            ReceptionForm.error_description,
            func.count(ReceptionForm.id)
        ).filter(ReceptionForm.created_date >= start, ReceptionForm.created_date <= end) \
         .group_by(ReceptionForm.error_description) \
         .order_by(func.count(ReceptionForm.id).desc()) \
         .limit(10)

        report_results['Loi Thuong Gap'] = [
            {'Mô tả lỗi': r[0] if r[0] else "Chưa xác định", 'Số lần xuất hiện': r[1]}
            for r in query.all()
        ]

    return report_results
if __name__ == "__main__":
    with app.app_context():
        print(load_customers())