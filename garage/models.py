import json
from enum import Enum

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DOUBLE, Enum as SQLEnum
from sqlalchemy.orm import relationship
from garage import db, app
from datetime import datetime

class UserRole(Enum):
    USER = 1
    TECHNICIAN = 2
    CASHIER = 3
    RECEPTIONIST = 4
    ADMIN = 5

class AppointmentStatus(Enum):
    BOOKED = 1
    CONFIRMED = 2
    CANCELLED = 3
    COMPLETED = 4

class VehicleStatus(Enum):
    PENDING_APPOINTMENT = 1 # đặt lịch, chưa đến gara
    RECEIVED = 2
    DIAGNOSING = 3  # đang kiểm tra
    WAITING_APPROVAL = 4  # chờ khách duyệt giá
    REPAIRING = 5
    DONE = 6
    DELIVERED = 7
    CANCELLED = 8


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now)

    def __str__(self):
        return getattr(self, "full_name", str(self.id))

class User(Base, UserMixin):
    username = Column(String(150), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    avatar = Column(
        String(300),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    customer = relationship("Customer", backref="user", uselist=False)
    employee = relationship("Employee", backref="user", uselist=False)

    def __str__(self):
        return f"{self.username}"


class Customer(Base):
    full_name = Column(String(255))
    phone = Column(String(10), nullable=False, unique=True)
    address = Column(String(255))
    vehicles = relationship("Vehicle", backref="customer", lazy=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)

class Employee(Base):
    full_name = Column(String(255))
    phone = Column(String(10), nullable=False, unique=True)
    receptions = relationship("ReceptionForm", backref="employee", lazy=True)
    repairs = relationship("RepairForm", backref="employee", lazy=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)

class Vehicle(Base):
    license_plate = Column(String(12), nullable=False, unique=True)
    vehicle_type = Column(String(50), nullable=False)
    vehicle_status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.PENDING_APPOINTMENT)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    receptions = relationship("ReceptionForm", backref="vehicle", lazy=True)

    def __str__(self):
        return f"{self.license_plate}"


class Appointment(Base):
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)

    schedule_time = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.BOOKED)
    note = Column(String(255))

    customer = relationship("Customer", backref="appointments")
    vehicle = relationship("Vehicle", backref="appointments")

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.schedule_time.strftime('%d/%m/%Y %H:%M')}"


class ReceptionForm(Base):
    error_description = Column(String(255))
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)

    repair_form = relationship("RepairForm", backref="reception_form", uselist=False)


class RepairForm(Base):
    reception_id = Column(Integer, ForeignKey("reception_form.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    details = relationship("RepairDetail", backref="repair_form", lazy=True,cascade="all, delete-orphan")
    invoice = relationship("Invoice", backref="repair_form", uselist=False)

    @property
    def calculate_total(self):
        return sum(d.total_cost for d in self.details)

class RepairDetail(Base):
    task = Column(String(255), nullable=False)
    labor_cost = Column(DOUBLE, nullable=False, default=0)
    service_id = Column(Integer, ForeignKey("service.id"))
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"))
    quantity = Column(Integer, nullable=False, default=1)

    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False)

    service = relationship("Service", lazy=True)

    @property
    def total_cost(self):
        total = 0

        if self.service:
            total += self.service.price
        total += self.labor_cost or 0
        if self.spare_part:
            total += (self.spare_part.unit_price or 0) * self.quantity
        return total


class SparePart(Base):
    name = Column(String(255), nullable=False)
    unit_price = Column(DOUBLE, nullable=False)
    unit = Column(String(50), nullable=False)
    supplier = Column(String(100), default=None)
    inventory = Column(Integer, default=None)
    image_url = Column(String(255),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )
    repair_details = relationship("RepairDetail", backref="spare_part", lazy=True)
    def __str__(self):
        return self.name


class Service(Base):
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(DOUBLE, nullable=False, default=0)
    image = Column(
        String(300),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )

    def __str__(self):
        return f"{self.name}"



class Invoice(Base):
    labor_total = Column(DOUBLE)
    parts_total = Column(DOUBLE)
    vat = Column(DOUBLE)
    total_payment = Column(DOUBLE)
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False, unique=True)

if __name__ == "__main__":
    with app.app_context():
        #db.create_all()
        with open("data/service.json", encoding="utf-8") as f:
            services = json.load(f)
            for s in services:
                ser = Service(**s)
                db.session.add(ser)

        with open("data/spare_parts.json", encoding="utf-8") as f:
            spare_parts = json.load(f)
            for sp in spare_parts:
                each_sp = SparePart(**sp)
                db.session.add(each_sp)


        db.session.commit()
