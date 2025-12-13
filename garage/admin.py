from flask import url_for, render_template
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.helpers import get_url
from flask_login import current_user
from markupsafe import Markup
from wtforms import DateTimeLocalField, IntegerField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from garage import app, db
from garage.models import (Service, Customer, Vehicle, User, Employee,
                           Appointment, RepairForm, ReceptionForm, SparePart,UserRole, RepairDetail)


class MyAdminHome(AdminIndexView):
    template = "admin/custom_master.html"
    # def is_accessible(self) -> bool:
    #     return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class MyAdminModelView(ModelView):
    list_template = "admin/list.html"
    # create_template = "admin/create1.html"
    #edit_template = "admin/edit1.html"
    # def is_accessible(self) -> bool:
    #     return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class ServiceAdmin(MyAdminModelView):
    column_list = ['name', 'description', 'active', 'price','created_date']
    column_labels = {
        'name': 'Tên dịch vụ',
        'description' : 'Mô tả',
        'active': 'Trạng thái',
        'price':'Giá',
        'created_date':'Ngày tạo'
    }
class CustomerAdmin(MyAdminModelView):
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

class EmployeeAdmin(MyAdminModelView):
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

class UserAdmin(MyAdminModelView):
    column_list = ['username',  'active', 'role','created_date']
    column_labels = {
        'username': 'Tên đăng nhập',
        'active':'Trạng thái',
        'role':'Vai trò',
        'created_date': 'Ngày tạo'
    }

class VehicleAdmin(MyAdminModelView):
    column_list = ['license_plate', 'vehicle_type', 'customer_id', 'vehicle_status', 'receptions']
    column_labels = {
        'license_plate': 'Biển số xe',
        'vehicle_type': 'Loại xe',
        #'vehicle_status': 'Trạng thái',
        'customer_id': 'Khách hàng',
        'receptions': 'Phiếu tiếp nhận'
    }
class AppointmentAdmin(MyAdminModelView):
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
    # Các cột hiển thị trong bảng
    column_list = ['id', 'employee', 'reception_form', 'vehicle_plate', 'created_date', 'total_money']
    column_labels = {
        'id': 'Mã phiếu sửa',
        'employee': 'Nhân viên lập',
        'reception_form': 'Phiếu tiếp nhận',
        'vehicle_plate': 'Biển số xe',
        'created_date': 'Ngày lập',
        'total_money': 'Tổng tiền',
    }

    form_columns = ['employee', 'reception_form', 'details']
    inline_models = [
        (RepairDetail, dict(
            form_columns=['id', 'task', 'service', 'spare_part', 'quantity', 'labor_cost'],
            form_label='Chi tiết sửa chữa',
            form_extra_fields={
                'quantity': IntegerField(default=1, validators=[DataRequired(), NumberRange(min=1)]),
                'labor_cost': DecimalField(default=0.0, places=2),
            },
            form_args={
                'id': {'label': 'ID', 'render_kw': {'readonly': True}},  # chỉ để admin biết pk
                'task': {'label': 'Công việc'},
                'service': {'label': 'Dịch vụ'},
                'spare_part': {'label': 'Phụ tùng'},
                'quantity': {'label': 'Số lượng'},
                'labor_cost': {'label': 'Tiền công'},
            }
        ))
    ]

    # Format các cột hiển thị trong bảng
    column_formatters = {
        'id': lambda v, c, m, p: Markup(
        f'<a href="{url_for("repair_detail.detail", repair_id=m.id)}">{m.id}</a>'
        ),

        'total_money': lambda v, c, m, p: f"{m.calculate_total:,.0f} ₫" if m.calculate_total else "0 ₫",
        'vehicle_plate': lambda v, c, m, p: (
            m.reception_form.vehicle.license_plate
            if m.reception_form and m.reception_form.vehicle else '-'
        ),
        'reception_form': lambda v, c, m, p: f"PTN {m.reception_form.id}" if m.reception_form else '-'
    }

class RepairDetailView(MyAdminHome):
    @expose('/<int:repair_id>')
    def detail(self, repair_id):
        repair = RepairForm.query.get_or_404(repair_id)
        return self.render('admin/custom_detail.html', repair=repair, enumerate=enumerate)

class RepairDetailFormAdmin(MyAdminModelView):
    column_list = ['id','repair_id','task','labor_cost', 'quantity',  'service']


class ReceptionFormAdmin(MyAdminModelView):
    column_list = ['id','employee', 'vehicle','error_description',  'repair_form']
    column_labels = {
        'id' : 'ID',
        'error_description': 'Lỗi',
        'employee': 'Nhân viên',
        'vehicle': 'Xe',
        'repair_form': 'Phiếu sửa chữa',
    }


class SparePartAdmin(MyAdminModelView):
    column_list = ['name','unit_price', 'unit','supplier','inventory']
    column_labels = {
        'name' : 'Tên',
        'unit_price': 'Giá',
        'unit': 'Đơn vị',
        'supplier': 'Nhà cung cấp',
        'inventory': 'Tồn kho'
    }

admin = Admin(app=app,name="GARAGE ADMIN",index_view=MyAdminHome(name="QUẢN TRỊ"))

admin.add_view(RepairDetailView(name="RD", endpoint="repair_detail"))


admin.add_view(ServiceAdmin(Service, db.session,name='DỊCH VỤ'))
admin.add_view(CustomerAdmin(Customer, db.session,name='KHÁCH HÀNG'))
admin.add_view(EmployeeAdmin(Employee, db.session,name='NHÂN VIÊN'))
admin.add_view(VehicleAdmin(Vehicle, db.session,name='XE'))
admin.add_view(UserAdmin(User, db.session,name='TÀI KHOẢN'))
admin.add_view(AppointmentAdmin(Appointment, db.session,name='LỊCH HẸN'))
admin.add_view(ReceptionFormAdmin(ReceptionForm, db.session,name='PHIẾU TIẾP NHẬN'))
admin.add_view(RepairFormAdmin(RepairForm, db.session,name='PHIẾU SỬA'))
admin.add_view(SparePartAdmin(SparePart, db.session,name='PHỤ TÙNG'))
admin.add_view(RepairDetailFormAdmin(RepairDetail, db.session,name='CHI TIẾT SỬA CHỮA'))

