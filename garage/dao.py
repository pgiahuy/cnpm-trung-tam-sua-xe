import hashlib
import json

from garage import db, app
from garage.models import User, Service, SparePart, Customer, UserRole, Vehicle, Appointment, AppointmentStatus
from datetime import datetime, date, time
from flask_login import current_user


def load_services():
    return Service.query.all()

def load_spare_parts():
    return SparePart.query.all()

def load_menu_items():
    with open("data/menu_items.json", encoding="utf-8") as f:
        return json.load(f)


def add_user(username, password, avatar, full_name, phone):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
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
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

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
