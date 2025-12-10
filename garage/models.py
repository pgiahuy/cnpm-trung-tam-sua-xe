from enum import Enum

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DOUBLE, Enum as SQLEnum
from sqlalchemy.orm import relationship
from garage import db, app
from datetime import datetime

class UserRole(Enum):
    USER = 1
    EMPLOYEE = 2
    ADMIN = 3

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
    full_name = Column(String(255))
    avatar = Column(
        String(300),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )
    Column(SQLEnum(UserRole), default=UserRole.USER)
    customer = relationship("Customer", backref="user", uselist=False)
    employee = relationship("Employee", backref="user", uselist=False)

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

class Vehicle(db.Model):
    license_plate = Column(String(12), primary_key=True)
    vehicle_type = Column(String(50), nullable=False)
    vehicle_status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.PENDING_APPOINTMENT)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    receptions = relationship("ReceptionForm", backref="vehicle", lazy=True)

class Appointment(Base):
    vehicle_plate = Column(String(12), ForeignKey("vehicle.license_plate"), nullable=False)
    schedule_time = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.BOOKED)
    note = Column(String(255))
    vehicle = relationship("Vehicle", backref="appointments", lazy=True)

class ReceptionForm(Base):
    error_description = Column(String(255))
    license_plate = Column(String(12), ForeignKey("vehicle.license_plate"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    repair_form = relationship("RepairForm", backref="reception_form", uselist=False)

class RepairForm(Base):
    reception_id = Column(Integer, ForeignKey("reception_form.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    total_cost = Column(DOUBLE, nullable=False)
    details = relationship("RepairDetail", backref="repair_form", lazy=True)
    invoice = relationship("Invoice", backref="repair_form", uselist=False)

    @property
    def calculate_total(self):
        total = 0
        for d in self.details:
            if d.service:
                total += d.service.price
            total += d.labor_cost
            if d.spare_part:
                total += d.spare_part.unit_price
        return total


class Invoice(Base):
    labor_total = Column(DOUBLE)
    parts_total = Column(DOUBLE)
    vat = Column(DOUBLE)
    total_payment = Column(DOUBLE)
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False, unique=True)

class SparePart(Base):
    unit_price = Column(DOUBLE)
    supplier = Column(String(100))
    repair_details = relationship("RepairDetail", backref="spare_part", lazy=True)

class RepairDetail(Base):
    task = Column(String(255), nullable=False)
    labor_cost = Column(DOUBLE, nullable=False)

    service_id = Column(Integer, ForeignKey("service.id"))
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"))
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False)

class Service(Base):
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(DOUBLE, nullable=False, default=0)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
