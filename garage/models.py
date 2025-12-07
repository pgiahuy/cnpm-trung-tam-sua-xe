from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, DOUBLE
from enum import Enum as RoleEnum
from sqlalchemy.orm import relationship
from garage import db, app
from datetime import datetime

class UserRole(RoleEnum):
    Customer = 1
    ADMIN = 2
    Employee=3

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime,default= datetime.now())

    def __str__(self):
        return self.name

class User(Base,UserMixin):
    username = Column(String(150), nullable=False ,unique=True)
    password = Column(String(150), nullable = False)
    avatar = Column(String(300), default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png")

class Customer(User,UserMixin):
    sdt=Column(String(10), nullable=False,unique=True)
    address=Column(String(100))
    user_role = Column(Enum(UserRole), default= UserRole.Customer)
    vehicles = relationship("Vehicle", backref="customer", lazy=True)

class Vehicle(db.Model):
    licensePlate = Column(String(12), primary_key=True)
    type=Column(String(50), nullable=False)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)

class Employee(User,UserMixin):
    user_role = Column(Enum(UserRole), default= UserRole.Employee)
    receptions = relationship("ReceptionForm", backref="employee", lazy=True)
    repairs = relationship("RepairForm", backref="employee", lazy=True)

class ReceptionForm(Base):
    errorDescription=Column(String(255))
    license_plate = Column(String(12), ForeignKey("vehicle.licensePlate"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    repair_form = relationship("RepairForm", backref="reception_form", uselist=False)

class Invoice(Base):
    issueDate = Column(DateTime, default=datetime.now)
    laborTotal=Column(DOUBLE)
    partsTotal=Column(DOUBLE)
    VAT=Column(DOUBLE)
    totalPayment=Column(DOUBLE)
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False, unique=True)

class RepairForm(Base):
    reception_id = Column(Integer, ForeignKey("reception_form.id"), nullable=False)
    totalCost = Column(DOUBLE, nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    details = relationship("RepairDetail", backref="repair_form", lazy=True)
    invoice = relationship("Invoice", backref="repair_form", uselist=False)

class SparePart(Base):
    unitPrice=Column(DOUBLE)
    supplier=Column(String(100), nullable=False)
    repair_details = relationship("RepairDetail", backref="spare_part", lazy=True)


class RepairDetail(Base):
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False)
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"))
    task=Column(String(255), nullable=False)
    laborCost=Column(DOUBLE,nullable=False)


if __name__=="__main__":
    with app.app_context():
        db.create_all()