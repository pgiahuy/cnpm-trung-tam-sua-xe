from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, DOUBLE
from sqlalchemy.orm import relationship
from enum import Enum as RoleEnum

from garage import db, app
from datetime import datetime

class UserRole(RoleEnum):
    USER = 1
    EMPLOYEE = 2
    ADMIN = 3


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now)

    def __str__(self):
        return getattr(self, "full_name", "id")


class User(Base, UserMixin):
    username = Column(String(150), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    full_name = Column(String(255))
    avatar = Column(
        String(300),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )
    role = Column(Enum(UserRole), default=UserRole.USER)
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
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    receptions = relationship("ReceptionForm", backref="vehicle", lazy=True)

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
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"))
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
