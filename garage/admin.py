from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField

from garage import app, db
from garage.models import Service, Customer, Vehicle, User


class MyAdminHome(AdminIndexView):
    template = "admin/master.html"

class MyAdminModelView(ModelView):
    list_template = "admin/list.html"
    create_template = "admin/create.html"
    edit_template = "admin/edit.html"

class ServiceAdmin(MyAdminModelView):
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


class UserAdmin(MyAdminModelView):
    column_list = ['username', 'avatar', 'active', 'role']
    column_labels = {
        'username': 'Tên đăng nhập',
        'avatar': 'Avatar',
        'active':'Trạng thái',
        'role':'Vai trò',
        'created_date': 'Ngày tạo'
    }

class VehicleAdmin(MyAdminModelView):
    column_list = ['license_plate', 'vehicle_type', 'customer_id', 'vehicle_status', 'receptions']
    column_labels = {
        'license_plate': 'Biển số xe',
        'vehicle_type': 'Loại xe',
        'vehicle_status': 'Trạng thái',
        'customer_id': 'Khách hàng',
        'receptions': 'Phiếu tiếp nhận'
    }


admin = Admin(
    app=app,
    name="GARAGE ADMIN",
    index_view=MyAdminHome(name="QUẢN TRỊ"),
)
admin.add_view(ServiceAdmin(Service, db.session,name='DỊCH VỤ'))
admin.add_view(CustomerAdmin(Customer, db.session,name='KHÁCH HÀNG'))
admin.add_view(VehicleAdmin(Vehicle, db.session,name='XE'))
admin.add_view(UserAdmin(User, db.session,name='TÀI KHOẢN'))