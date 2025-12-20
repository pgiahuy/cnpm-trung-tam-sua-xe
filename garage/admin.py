from datetime import date, datetime

from flask import url_for, render_template, redirect, request, send_file, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField

from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func
from wtforms import DateTimeLocalField, IntegerField, DecimalField, SelectField, StringField, RadioField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Optional
from garage import db, app, dao
from garage.models import (Service, Customer, Vehicle, User, Employee,
                           Appointment, RepairForm, ReceptionForm, SparePart, UserRole, RepairDetail, AppointmentStatus,
                           VehicleStatus, SystemConfig, RepairStatus)
import json
import pandas as pd
import io


class AdminAccessMixin:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN
    def is_visible(self):
        return self.is_accessible()

class MyAdminHome(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self=None, *args, **kwargs):
        instance = self or kwargs.get('cls')
        if request.method == 'POST':
            sections = request.form.getlist('sections')

            start_date_str = request.form.get('startDate')
            end_date_str = request.form.get('endDate')
            today = datetime.now()

            if not start_date_str:
                start_date_str = today.replace(day=1).strftime('%Y-%m-%d')

            if not end_date_str:
                end_date_str = today.strftime('%Y-%m-%d')

            data = dao.get_report_data(start_date_str, end_date_str, sections)

            if not any(data.values()):
                flash("Không có dữ liệu trong khoảng thời gian đã chọn!", "warning")
                return redirect(url_for('admin.index'))

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, content in data.items():
                    if content:
                        df = pd.DataFrame(content)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                        worksheet = writer.sheets[sheet_name]
                        for i, col in enumerate(df.columns):
                            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                            worksheet.set_column(i, i, column_len)

            output.seek(0)
            return send_file(
                output,
                download_name=f"Bao_cao_Tong_hop_{start_date_str}_den_{end_date_str}.xlsx",
                as_attachment=True,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        max_slot_obj = SystemConfig.query.get('MAX_SLOT_PER_DAY')
        max_slot = int(max_slot_obj.value) if max_slot_obj else 30
        repairing = Vehicle.query.filter_by(vehicle_status='REPAIRING').count()

        try:
            vat = dao.get_vat_value()
        except:
            vat = 0.1

        today = date.today()
        slots_today = ReceptionForm.query.filter(
            func.date(ReceptionForm.created_date) == today
        ).count()

        revenue_day_raw = dao.get_revenue_by_day()
        revenue_month_raw = dao.get_revenue_by_month()
        vehicle_stats_raw = dao.get_vehicle_stats()
        error_stats_raw = dao.get_error_stats()

        def format_chart_data(data):
            if isinstance(data, dict): return data
            try:
                return {str(row[0]): row[1] for row in data}
            except:
                return {}

        return instance.render('admin/index.html',
                               vat=vat,
                               slots_today=slots_today,
                               max_slot=max_slot,
                               repairing=repairing,
                               revenue_day=json.dumps(format_chart_data(revenue_day_raw)),
                               revenue_month=json.dumps(format_chart_data(revenue_month_raw)),
                               vehicle_stats=json.dumps(format_chart_data(vehicle_stats_raw)),
                               error_stats=json.dumps(format_chart_data(error_stats_raw)))


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
    can_create = False
    column_list = ['license_plate', 'vehicle_type', 'customer', 'vehicle_status', 'receptions']
    column_labels = {
        'license_plate': 'Biển số xe',
        'vehicle_type': 'Loại xe',
        #'vehicle_status': 'Trạng thái',
        'customer': 'Khách hàng',
        'receptions': 'Phiếu tiếp nhận'
    }
class AppointmentAdmin(AdminAccessMixin,MyAdminModelView):
    can_create = False
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


class ReceptionFormAdmin(MyAdminModelView):
    create_template = 'admin/reception_form.html'
    edit_template = 'admin/reception_form.html'
    extra_js = [
        '/static/js/receive_form.js'
    ]
    column_list = ['id','customer','vehicle','employee','receive_type','error_description']
    column_labels = {
        'id': 'ID',
        'customer': 'Khách hàng',
        'vehicle': 'Biển số xe',
        'employee': 'Nhân viên tiếp nhận',
        'error_description': 'Mô tả lỗi',
        'receive_type':'Lịch hẹn'
    }

    column_formatters = {
        'customer': lambda v, c, m, p: (m.vehicle.customer.full_name if m.vehicle and m.vehicle.customer else ''),
        'receive_type': lambda v, c, m, p: ('Có' if m.receive_type == 'appointment' else 'Không')

    }

    form_columns = [
        'receive_type',
        'employee',

        'appointment_id',

        'customer_id',
        'is_new_customer',
        'new_customer_name',
        'new_customer_phone',

        'vehicle_id',
        'is_new_vehicle',
        'new_vehicle_plate',
        'new_vehicle_type',

        'error_description'
    ]

    form_extra_fields = {

        'receive_type': RadioField(
            'Hình thức tiếp nhận',
            choices=[('appointment', 'ĐÃ ĐẶT LỊCH'), ('walk_in', 'CHƯA ĐẶT LỊCH')],
            default='appointment',
            validators=[DataRequired()]
        ),

        'employee': QuerySelectField(
            'Nhân viên',
            query_factory=lambda: db.session.query(Employee).all(),
            get_label='full_name',
            validators=[DataRequired()]
        ),

        'appointment_id': SelectField(
            'Chọn lịch đã đặt',
            coerce=lambda x: int(x) if x else None,
            validators=[Optional()]
        ),

        'customer_id': SelectField(
            'Chọn khách hàng',
            coerce=lambda x: int(x) if x else None,
            validators=[Optional()]
        ),
        'vehicle_id': SelectField(
            'Chọn xe',
            coerce=lambda x: int(x) if x else None,
            validators=[Optional()]
        ),

        'is_new_customer': BooleanField('Khách hàng mới'),
        'is_new_vehicle': BooleanField('Xe mới'),

        'new_customer_name': StringField('Tên khách mới'),
        'new_customer_phone': StringField('SĐT khách mới'),

        'new_vehicle_plate': StringField('Biển số xe mới'),
        'new_vehicle_type': StringField('Loại xe mới'),

        'error_description': StringField('Mô tả lỗi'),
    }

    def create_form(self):
        form = super().create_form()
        self._populate_choices(form)
        return form

    def edit_form(self):
        form = super().edit_form()
        self._populate_choices(form)
        return form

    def _populate_choices(self, form):
        form.customer_id.choices = [('', '-- Chọn khách hàng --')] + [
            (c.id, f"{c.full_name} - {c.phone}")
            for c in Customer.query.order_by(Customer.full_name).all()
        ]

        appointments = Appointment.query.filter_by(status=AppointmentStatus.CONFIRMED).all()
        form.appointment_id.choices = [('', '-- Chọn lịch hẹn --')] + [
            (a.id, f"{a.vehicle.license_plate} - {a.customer.full_name} ({a.schedule_time.strftime('%d/%m %H:%M')})")
            for a in appointments
        ]

        form.vehicle_id.choices = [('', '-- Chọn xe --')]

        return form

    def on_model_change(self, form, model, is_created):
        try:
            with db.session.no_autoflush:
                receive_type = form.receive_type.data
                model.employee_id = form.employee.data.id
                model.error_description = form.error_description.data or ""
                model.receive_type = receive_type

                if receive_type == "appointment": # có lịch hẹn
                    if not form.appointment_id.data:
                        raise ValueError("Vui lòng chọn phiếu hẹn!")

                    appointment = db.session.get(Appointment, int(form.appointment_id.data))
                    if not appointment:
                        raise ValueError("Phiếu hẹn không tồn tại!")


                    vehicle = appointment.vehicle

                    appointment.status = AppointmentStatus.COMPLETED
                    vehicle.vehicle_status = VehicleStatus.RECEIVED

                    db.session.add(appointment)
                    db.session.add(vehicle)

                else:  # walk_in
                    if form.is_new_customer.data:
                        if not form.new_customer_name.data or not form.new_customer_phone.data:
                            raise ValueError("Vui lòng nhập tên và số điện thoại khách mới!")

                        customer = Customer(
                            full_name=form.new_customer_name.data.strip(),
                            phone=form.new_customer_phone.data.strip(),
                            active=True
                        )
                        db.session.add(customer)
                    else:
                        if not form.customer_id.data:
                            raise ValueError("Vui lòng chọn khách hàng!")
                        customer = db.session.get(Customer, int(form.customer_id.data))


                    # === Xe ===
                    if form.is_new_vehicle.data:
                        if not form.new_vehicle_plate.data or not form.new_vehicle_type.data:
                            raise ValueError("Vui lòng nhập biển số và loại xe mới!")

                        plate = form.new_vehicle_plate.data.strip().upper()
                        if Vehicle.query.filter_by(license_plate=plate).first():
                            raise ValueError(f"Biển số {plate} đã tồn tại!")

                        vehicle = Vehicle(
                            license_plate=plate,
                            vehicle_type=form.new_vehicle_type.data.strip(),
                            vehicle_status=VehicleStatus.RECEIVED,
                            customer=customer
                        )
                        db.session.add(vehicle)
                    else:
                        if not form.vehicle_id.data:
                            raise ValueError("Vui lòng chọn xe!")
                        vehicle = db.session.get(Vehicle, int(form.vehicle_id.data))
                        # if not vehicle:
                        #     raise ValueError("Xe không tồn tại!")
                        # if vehicle.customer_id != customer.id:
                        #     raise ValueError("Xe không thuộc khách hàng này!")

                        vehicle.vehicle_status = VehicleStatus.RECEIVED
                        db.session.add(vehicle)

                # === QUAN TRỌNG NHẤT: Gán object vehicle cho model ===
                model.vehicle = vehicle  # <--- Dòng này fix tất cả!

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Lỗi tạo phiếu: {str(e)}")



class RepairFormAdmin(MyAdminModelView):
    column_list = ['id', 'employee', 'reception_form', 'repair_status','vehicle_plate', 'total_money']
    column_labels = {
        'id': 'Mã phiếu sửa',
        'employee': 'Nhân viên lập',
        'reception_form': 'PTN',
        'vehicle_plate': 'Biển số xe',
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

    REPAIR_TO_VEHICLE_STATUS = {
        "QUOTED": VehicleStatus.WAITING_APPROVAL,
        "REPAIRING": VehicleStatus.REPAIRING,
        "DONE": VehicleStatus.DONE,
        "PAID": VehicleStatus.DELIVERED
    }

    def on_model_change(self, form, model, is_created):
        with db.session.no_autoflush:

            if not model.reception_form or not model.reception_form.vehicle:
                raise ValueError("Phiếu tiếp nhận chưa gắn xe")

            if is_created:
                model.vehicle = model.reception_form.vehicle

            for detail in model.details:
                if detail.service:
                    detail.service_price = detail.service.price
                if detail.spare_part:
                    detail.spare_part_price = detail.spare_part.unit_price

            new_vehicle_status = self.REPAIR_TO_VEHICLE_STATUS.get(model.repair_status)

            if new_vehicle_status and model.vehicle.vehicle_status != new_vehicle_status:
                model.vehicle.vehicle_status = new_vehicle_status
                db.session.add(model.vehicle)

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


    # def on_model_change(self, form, model, is_created):
    #     try:
    #         if form.appointment_id.data:
    #
    #             appointment = db.session.get(Appointment, form.appointment_id.data)
    #             if not appointment:
    #                 raise ValueError("Lịch không hợp lệ.")
    #
    #             vehicle = appointment.vehicle
    #             customer = vehicle.customer
    #
    #             appointment.status = AppointmentStatus.COMPLETED
    #             db.session.add(appointment)
    #
    #             vehicle.vehicle_status = VehicleStatus.RECEIVED
    #             db.session.add(vehicle)
    #
    #         else:
    #             # === khôgn có lịch (lại CH tiếp nhận) ===
    #             if form.new_customer.data:
    #                 customer = db.session.query(Customer).filter_by(phone=form.new_customer_phone.data).first()
    #                 if not customer:
    #                     customer = Customer(
    #                         full_name=form.new_customer.data,
    #                         phone=form.new_customer_phone.data
    #                     )
    #                     db.session.add(customer)
    #                     db.session.flush()
    #             elif form.customer_id.data:
    #                 customer = db.session.get(Customer, form.customer_id.data)
    #             else:
    #                 raise ValueError("Phải chọn khách hàng hoặc nhập khách hàng mới.")
    #
    #             if form.new_vehicle_plate.data:
    #                 vehicle = Vehicle(
    #                     license_plate=form.new_vehicle_plate.data,
    #                     vehicle_type=form.new_vehicle_type.data or "unknown",
    #                     vehicle_status=VehicleStatus.RECEIVED,
    #                     customer_id=customer.id
    #                 )
    #                 db.session.add(vehicle)
    #                 db.session.flush()
    #             elif form.vehicle_id.data:
    #                 vehicle = db.session.get(Vehicle, form.vehicle_id.data)
    #
    #                 # xe chuyển sang RECEIVED
    #                 vehicle.vehicle_status = VehicleStatus.RECEIVED
    #                 db.session.add(vehicle)
    #             else:
    #                 raise ValueError("Phải chọn xe hoặc nhập xe mới.")
    #
    #         # Gán cho phiếu tiếp nhận
    #         model.vehicle_id = vehicle.id
    #         model.employee_id = (
    #             current_user.employee.id
    #             if hasattr(current_user, 'employee') and current_user.employee
    #             else form.employee.data.id
    #         )
    #
    #         db.session.add(model)
    #
    #     except Exception as e:
    #         db.session.rollback()
    #         raise e


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


