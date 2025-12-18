from datetime import date

from flask import url_for, render_template, redirect
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField

from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func
from wtforms import DateTimeLocalField, IntegerField, DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional
from garage import db, app, dao
from garage.models import (Service, Customer, Vehicle, User, Employee,
                           Appointment, RepairForm, ReceptionForm, SparePart, UserRole, RepairDetail, AppointmentStatus,
                           VehicleStatus, SystemConfig)


class AdminAccessMixin:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN
    def is_visible(self):
        return self.is_accessible()

class MyAdminHome(AdminIndexView):


    @expose('/')
    def index(self):
        max_slot_obj = SystemConfig.query.filter_by(id='MAX_SLOT_PER_DAY').first()
        repairing = Vehicle.query.filter_by(vehicle_status='REPAIRING').count()

        vat = dao.get_vat_value()
        max_slot = int(max_slot_obj.value)

        today = date.today()
        slots_today = ReceptionForm.query.filter(
            func.date(ReceptionForm.created_date) == today
        ).count()
        return self.render('admin/index.html',vat=vat, slots_today=slots_today, max_slot=max_slot, repairing=repairing)

    #template = 'admin/custom_master.html'
    #base_template = 'admin/custom_base.html'
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in (
            UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.CASHIER, UserRole.TECHNICIAN
        )
    def inaccessible_callback(self, name, **kwargs):
        # Nếu không có quyền, trả về trang 403
        return render_template('errors/403.html'), 403




class MyAdminModelView(ModelView):
    list_template = "admin/list.html"

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role in (
            UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.CASHIER, UserRole.TECHNICIAN
        )

    def inaccessible_callback(self, name, **kwargs):
        # Nếu không có quyền, trả về trang 403
        return render_template('errors/403.html'), 403


class ServiceAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['name', 'description', 'active', 'price','created_date']
    column_labels = {
        'name': 'Tên dịch vụ',
        'description' : 'Mô tả',
        'active': 'Trạng thái',
        'price':'Giá',
        'created_date':'Ngày tạo'
    }
class CustomerAdmin(AdminAccessMixin,MyAdminModelView):
    column_labels = {
        'full_name': 'Họ tên',
        'phone' : 'Số điện thoại',
        'address': 'Địa chỉ',
        'active':'Trạng thái',
        'price':'Giá',
        'created_date':'Ngày tạo',
        'user': 'Tài khoản'
    }
    column_formatters = {
        'user': lambda v, c, m, p: m.user.username if m.user else ''
    }
    form_extra_fields = {
        'user': QuerySelectField(
            'User',
            query_factory=lambda: db.session.query(User).all(),
            get_label='username'
        )
    }

class EmployeeAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['full_name',  'phone','active', 'user']
    column_labels = {
        'full_name': 'Họ tên',
        'phone' : 'Số điện thoại',
        'active':'Trạng thái',
        'created_date':'Ngày tạo',
        'user': 'Tài khoản'

    }
    column_formatters = {
        'user': lambda v, c, m, p: m.user.username if m.user else ''
    }

class UserAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['username',  'active', 'role','created_date']
    column_labels = {
        'username': 'Tên đăng nhập',
        'active':'Trạng thái',
        'role':'Vai trò',
        'created_date': 'Ngày tạo'
    }

class VehicleAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['license_plate', 'vehicle_type', 'customer', 'vehicle_status', 'receptions']
    column_labels = {
        'license_plate': 'Biển số xe',
        'vehicle_type': 'Loại xe',
        #'vehicle_status': 'Trạng thái',
        'customer': 'Khách hàng',
        'receptions': 'Phiếu tiếp nhận'
    }
class AppointmentAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['customer', 'vehicle', 'schedule_time', 'status', 'note']
    column_labels = {
        'customer': 'Khách',
        'vehicle': 'Xe',
        'schedule_time': 'Ngày hẹn',
        'status': 'Trạng thái',
        'note': 'Ghi chú'
    }
    form_overrides = {
        'schedule_time': DateTimeLocalField,
    }
    form_args = {
        'schedule_time': {
            'format': '%Y-%m-%dT%H:%M'
        }
    }

class RepairFormAdmin(MyAdminModelView):
    column_list = ['id', 'employee', 'reception_form', 'repair_status','vehicle_plate', 'created_date', 'total_money']
    column_labels = {
        'id': 'Mã phiếu sửa',
        'employee': 'Nhân viên lập',
        'reception_form': 'Phiếu tiếp nhận',
        'vehicle_plate': 'Biển số xe',
        'created_date': 'Ngày lập',
        'total_money': 'Tổng tiền',
        'repair_status':'Trạng thái'
    }

    form_columns = ['employee', 'reception_form','repair_status', 'details']
    inline_models = [
        (RepairDetail, dict(
            form_columns=['id', 'task', 'service', 'spare_part', 'quantity'],
            form_label='Chi tiết sửa chữa',
            form_extra_fields={
                'quantity': IntegerField(default=1, validators=[DataRequired(), NumberRange(min=1)]),
                'labor_cost': DecimalField(default=0.0, places=2),
            },
            form_args={
                'id': {'label': 'ID', 'render_kw': {'readonly': True}},
                'task': {'label': 'Công việc'},
                'service': {'label': 'Dịch vụ'},
                'spare_part': {'label': 'Phụ tùng'},
                'quantity': {'label': 'Số lượng'},
            }
        ))
    ]

    #lấy giá tại thời điểm tạo
    def on_model_change(self, form, model, is_created):
        for detail in model.details:
            if detail.service:
                detail.service_price = detail.service.price
            if detail.spare_part:
                detail.spare_part_price = detail.spare_part.unit_price

    column_formatters = {
        'id': lambda v, c, m, p: Markup(
        f'<a href="{url_for("repair_detail.detail", repair_id=m.id)}">{m.id}</a>'
        ),

        'total_money': lambda v, c, m, p: f"{m.total_before_vat:,.0f} ₫" if m.total_before_vat else "0 ₫",
        'vehicle_plate': lambda v, c, m, p: (
            m.reception_form.vehicle.license_plate
            if m.reception_form and m.reception_form.vehicle else '-'
        ),
        'reception_form': lambda v, c, m, p: f"PTN {m.reception_form.id}" if m.reception_form else '-'
    }
    form_extra_fields = {
        'reception_form': QuerySelectField(
            'Chọn phiếu tiếp nhận',
            query_factory=lambda: db.session.query(ReceptionForm).all(),
            get_label=lambda r: f"[{r.vehicle.license_plate}] - [{r.created_date}] - [{r.vehicle.customer}]" if r.vehicle else f"PTN {r.id}",
            allow_blank=True,
            validators=[DataRequired()]
        ),
    }

# class RepairDetailView(BaseView):
#     @expose('/<int:repair_id>')
#     def detail(self, repair_id,**kwargs):
#         repair = RepairForm.query.get_or_404(repair_id)
#         return self.render('admin/custom_detail.html', repair=repair, enumerate=enumerate)
class RepairDetailView(BaseView):

    @expose('/')
    def index(self):
        return redirect(url_for('admin.index'))

    @expose('/<int:repair_id>')
    def detail(self, repair_id, **kwargs):
        repair = RepairForm.query.get_or_404(repair_id)
        return self.render(
            'admin/custom_detail.html',
            repair=repair,
            enumerate=enumerate
        )


class ReceptionFormAdmin(MyAdminModelView):
    column_list = ['id','customer','vehicle','employee','error_description']
    column_labels = {
        'id': 'ID',
        'customer': 'Khách hàng',
        'vehicle': 'Biển số xe',
        'employee': 'Nhân viên tiếp nhận',
        'error_description': 'Mô tả lỗi',
    }

    column_formatters = {
        'customer': lambda v, c, m, p: m.vehicle.customer.full_name if m.vehicle and m.vehicle.customer else ''
    }

    form_columns = ['employee', 'appointment_id', 'customer_id', 'new_customer', 'new_customer_phone',
                    'vehicle_id', 'new_vehicle_plate', 'new_vehicle_type', 'error_description']

    form_extra_fields = {
        'employee': QuerySelectField(
            'Nhân viên',
            query_factory=lambda: db.session.query(Employee).all(),
            get_label='full_name',
            validators=[DataRequired()]
        ),
        'appointment_id': SelectField('Chọn lịch đã đặt', coerce=int, validators=[Optional()]),
        'customer_id': SelectField('Chọn khách hàng', coerce=int, validators=[Optional()]),
        'vehicle_id': SelectField('Chọn xe', coerce=int, validators=[Optional()]),
        'new_customer': StringField('Tên khách hàng mới'),
        'new_customer_phone': StringField('SĐT khách mới'),
        'new_vehicle_plate': StringField('Biển số xe mới'),
        'new_vehicle_type': StringField('Loại xe mới'),
        'error_description': StringField('Lỗi')
    }

    def create_form(self, obj=None):
        form = super().create_form(obj)
        # Load tất cả khách hàng
        form.customer_id.choices = [(c.id, c.full_name) for c in db.session.query(Customer).all()]
        # Load tất cả xe có appointment confirmed
        appointments = db.session.query(Appointment).filter_by(status=AppointmentStatus.CONFIRMED).all()
        form.appointment_id.choices = [(a.id, f"{a.vehicle.license_plate} ({a.customer.full_name})") for a in appointments]
        form.vehicle_id.choices = [(a.vehicle.id, a.vehicle.license_plate) for a in appointments]
        return form

    def on_model_change(self, form, model, is_created):
        try:
            if form.appointment_id.data:
                # Trường hợp có lịch đã đặt
                appointment = db.session.query(Appointment).get(form.appointment_id.data)
                if not appointment:
                    raise ValueError("Lịch không hợp lệ.")
                vehicle = appointment.vehicle
                customer = vehicle.customer
                appointment.status = AppointmentStatus.COMPLETED
                db.session.add(appointment)
            else:
                # Xử lý khách hàng mới/cũ
                if form.new_customer.data:
                    customer = db.session.query(Customer).filter_by(phone=form.new_customer_phone.data).first()
                    if not customer:
                        customer = Customer(
                            full_name=form.new_customer.data,
                            phone=form.new_customer_phone.data
                        )
                        db.session.add(customer)
                        db.session.flush()
                elif form.customer_id.data:
                    customer = db.session.query(Customer).get(form.customer_id.data)
                else:
                    raise ValueError("Phải chọn khách hàng hoặc nhập khách hàng mới.")

                # Xử lý xe mới/cũ
                if form.new_vehicle_plate.data:
                    vehicle = Vehicle(
                        license_plate=form.new_vehicle_plate.data,
                        vehicle_type=form.new_vehicle_type.data or "unknown",
                        vehicle_status=VehicleStatus.RECEIVED,
                        customer_id=customer.id
                    )
                    db.session.add(vehicle)
                    db.session.flush()
                elif form.vehicle_id.data:
                    vehicle = db.session.query(Vehicle).get(form.vehicle_id.data)
                else:
                    raise ValueError("Phải chọn xe hoặc nhập xe mới.")

            # Gán cho model
            model.vehicle_id = vehicle.id
            model.employee_id = current_user.employee.id if hasattr(current_user,
                                                                    'employee') and current_user.employee else form.employee.data.id
            db.session.add(model)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e


class SparePartAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['name','unit_price', 'unit','supplier','inventory']
    column_labels = {
        'name' : 'Tên',
        'unit_price': 'Giá',
        'unit': 'Đơn vị',
        'supplier': 'Nhà cung cấp',
        'inventory': 'Tồn kho'
    }


class SystemConfigAdmin(AdminAccessMixin,MyAdminModelView):
    column_list = ['id','value']
    form_columns = ['id', 'value']
    can_delete = False
    column_labels = {
        'id' : 'Quy định',
        'value' : 'Giá trị'
    }




admin = Admin(app=app, name='GARAGE ADMIN',index_view=MyAdminHome(name='TRANG CHỦ'))


admin.add_view(UserAdmin(User, db.session,name='TÀI KHOẢN'))
admin.add_view(CustomerAdmin(Customer, db.session,name='KHÁCH HÀNG'))
admin.add_view(EmployeeAdmin(Employee, db.session,name='NHÂN VIÊN'))
admin.add_view(AppointmentAdmin(Appointment, db.session,name='LỊCH HẸN'))
admin.add_view(ReceptionFormAdmin(ReceptionForm, db.session,name='PHIẾU TIẾP NHẬN'))
admin.add_view(RepairFormAdmin(RepairForm, db.session,name='PHIẾU SỬA CHỮA'))
admin.add_view(VehicleAdmin(Vehicle, db.session,name='XE'))
admin.add_view(ServiceAdmin(Service, db.session,name='DỊCH VỤ'))
admin.add_view(SparePartAdmin(SparePart, db.session,name='PHỤ TÙNG'))
admin.add_view(SystemConfigAdmin(SystemConfig, db.session,name='QUY ĐỊNH'))

admin.add_view(RepairDetailView(name="CHI TIẾT SỬA CHỮA", endpoint="repair_detail"))


