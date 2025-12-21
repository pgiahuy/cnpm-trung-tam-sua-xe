import hashlib
import json
from enum import Enum

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DOUBLE, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from garage import db, app, dao
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
    RECEIVED = 2 # đã lập phiếu tiếp nhận
    DIAGNOSING = 3  # đang kiểm tra| xoá cái này
    WAITING_APPROVAL = 4  # chờ khách duyệt giá; đã lập phiếu sửa chữa
    REPAIRING = 5 #
    DONE = 6 # có thể thanh toán
    DELIVERED = 7 # đã thanh toán
    CANCELLED = 8

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class RepairStatus(Enum):
    QUOTED = "QUOTED"
    APPROVED = "APPROVED"
    REPAIRING = "REPAIRING"
    DONE = "DONE"
    PAID = "PAID"

class ReceiptItemType(Enum):
    SERVICE = "SERVICE"
    SPARE_PART = "SPARE_PART"

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
    comments = relationship("Comment", backref="user", lazy=True)

    def __str__(self):
        return f"{self.username}"


class Customer(Base):
    full_name = Column(String(255))
    phone = Column(String(10), nullable=False, unique=True)
    address = Column(String(255))
    vehicles = relationship("Vehicle", backref="customer", lazy=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    receipts = relationship("Receipt", backref="customer", lazy=True, cascade="all, delete-orphan")

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
    repair_forms = relationship("RepairForm", backref="vehicle")

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
    receive_type = db.Column(db.String(20), default='appointment')
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    repair_form = relationship("RepairForm", backref="reception_form", uselist=False)



class RepairForm(Base):
    reception_id = Column(Integer, ForeignKey("reception_form.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    repair_status = Column(SQLEnum(RepairStatus), default=RepairStatus.QUOTED)
    details = relationship("RepairDetail",backref="repair_form",cascade="all, delete-orphan")
    receipt = relationship("Receipt", backref="repair_form", uselist=False)

    @property
    def total_before_vat(self):
        return sum(d.total_cost for d in self.details)



class SparePart(Base):
    name = Column(String(255), nullable=False)
    unit_price = Column(DOUBLE, nullable=False)
    unit = Column(String(50), nullable=False)
    supplier = Column(String(100), default=None)
    inventory = Column(Integer, default=None)
    image_url = Column(String(255),
        default="https://icons.iconarchive.com/icons/papirus-team/papirus-status/256/avatar-default-icon.png"
    )
    repair_details = relationship(
        "RepairDetail",
        back_populates="spare_part",
        lazy=True
    )
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

class RepairDetail(Base):
    task = Column(String(255), nullable=False)

    service_id = Column(Integer, ForeignKey("service.id"))
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"))

    quantity = Column(Integer, nullable=False, default=1)
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=False)

    service = relationship("Service", lazy=True)
    spare_part = relationship(
        "SparePart",
        back_populates="repair_details",
        lazy=True
    )

    service_price = Column(DOUBLE, nullable=True)
    spare_part_price = Column(DOUBLE, nullable=True)

    @property
    def total_cost(self):
        total = 0
        if self.service_price:
            total += self.service_price
        if self.spare_part_price:
            total += self.spare_part_price * self.quantity

        return total

    @classmethod
    def create(cls, task, service=None, spare_part=None, quantity=1, repair_id=None):
        service_price = service.price if service else 0
        spare_part_price = spare_part.unit_price if spare_part else 0
        return cls(task=task,service=service,spare_part=spare_part,quantity=quantity,repair_id=repair_id,
                   service_price=service_price, spare_part_price=spare_part_price)

class Invoice(Base):
    receipt_id = Column(Integer, ForeignKey("receipt.id"), nullable=False, unique=True)

    invoice_number = Column(String(50), unique=True)
    company_name = Column(String(255))
    tax_code = Column(String(20))
    company_address = Column(String(255))

    issued_date = Column(DateTime, default=datetime.now)


class Receipt(Base):
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=True, unique=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    subtotal = Column(DOUBLE, nullable=False)
    vat_rate = Column(DOUBLE, default=0)
    type = Column(SQLEnum("REPAIR", "BUY"),default="REPAIR")
    total_paid = Column(DOUBLE, nullable=False)
    payment_method = Column(String(50))
    paid_at = Column(DateTime, default=datetime.now)

    invoice = relationship("Invoice", backref="receipt", uselist=False)
    items = relationship("ReceiptItem",backref="receipt",cascade="all, delete-orphan")

class ReceiptItem(Base):
    receipt_id = Column(Integer, ForeignKey("receipt.id"), nullable=True)
    repair_detail_id = Column(Integer, ForeignKey("repair_detail.id"), nullable=True)

    item_type = Column(SQLEnum(ReceiptItemType), default=ReceiptItemType.SPARE_PART)

    service_id = Column(Integer, ForeignKey("service.id"), nullable=True)
    service = relationship("Service", lazy=True)
    spare_part_id = Column(Integer, ForeignKey("spare_part.id"), nullable=True)
    spare_part = relationship("SparePart", backref="receipt_details", lazy=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(DOUBLE, nullable=False)
    total_price = Column(DOUBLE, nullable=False)

class Payment(Base):
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    receipt_id = Column(Integer, ForeignKey("receipt.id"), nullable=True)
    repair_id = Column(Integer, ForeignKey("repair_form.id"), nullable=True)
    type = Column(SQLEnum("REPAIR", "BUY"), default="REPAIR")
    amount = Column(DOUBLE, nullable=False)
    method = Column(String(50), default="VNPAY")
    vat_rate = Column(DOUBLE, default=0)
    transaction_ref = Column(String(100), unique=True)      # txn_ref gửi VNPAY
    vnp_transaction_no = Column(String(100))                # mã VNPAY trả về

    status = Column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING
    )
    user = relationship("User")
    receipt = relationship("Receipt", backref="payment", uselist=False)
    repair = relationship("RepairForm", backref="payments")
    cart_snapshot = db.Column(Text, nullable=True)

class Comment(Base):
    content = Column(String(255), nullable=False)
    sparepart_id = Column(Integer, ForeignKey("spare_part.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)


class SystemConfig(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(100), nullable=False)

