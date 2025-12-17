import json
from garage.models import *

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # --- Services ---
        with open("data/service.json", encoding="utf-8") as f:
            services = []
            for s in json.load(f):
                service = Service(**s)
                db.session.add(service)
                services.append(service)
        db.session.commit()  # commit để có id thực tế

        with open("data/spare_parts.json", encoding="utf-8") as f:
            spare_parts = []
            for s in json.load(f):
                spare_part = SparePart(**s)
                db.session.add(spare_part)
                spare_parts.append(spare_part)
        db.session.commit()  # commit để có id thực tế

        # --- Users ---
        users = []
        with open("data/user.json", encoding="utf-8") as f:
            for u in json.load(f):
                user = User(**u)
                db.session.add(user)
                users.append(user)
        db.session.commit()

        # --- Customers ---
        customers = []
        with open("data/customer.json", encoding="utf-8") as f:
            for idx, c in enumerate(json.load(f)):
                c['user_id'] = users[idx % len(users)].id  # gán user_id hợp lệ
                cust = Customer(**c)
                db.session.add(cust)
                customers.append(cust)
        db.session.commit()

        # --- Vehicles ---
        vehicles = []
        with open("data/vehicle.json", encoding="utf-8") as f:
            for idx, v in enumerate(json.load(f)):
                v['customer_id'] = customers[idx % len(customers)].id  # gán customer_id hợp lệ
                veh = Vehicle(**v)
                db.session.add(veh)
                vehicles.append(veh)
        db.session.commit()

        # --- Employees ---
        employees = []
        with open("data/employee.json", encoding="utf-8") as f:
            for idx, e in enumerate(json.load(f)):
                e['user_id'] = users[(idx + 1) % len(users)].id  # gán user_id hợp lệ
                emp = Employee(**e)
                db.session.add(emp)
                employees.append(emp)
        db.session.commit()

        # --- Appointments ---
        with open("data/appointment.json", encoding="utf-8") as f:
            for idx, a in enumerate(json.load(f)):
                a['customer_id'] = customers[idx % len(customers)].id
                a['vehicle_id'] = vehicles[idx % len(vehicles)].id
                db.session.add(Appointment(**a))
        db.session.commit()

        # --- ReceptionForms ---
        with open("data/reception_form.json", encoding="utf-8") as f:
            for idx, r in enumerate(json.load(f)):
                r['vehicle_id'] = vehicles[idx % len(vehicles)].id
                r['employee_id'] = employees[idx % len(employees)].id
                db.session.add(ReceptionForm(**r))
        db.session.commit()

        # --- RepairForms ---
        with open("data/repair_form.json", encoding="utf-8") as f:
            for idx, rf in enumerate(json.load(f)):
                rf['reception_id'] = idx + 1
                rf['employee_id'] = employees[idx % len(employees)].id
                db.session.add(RepairForm(**rf))
        db.session.commit()

        # --- RepairDetails ---
        with open("data/repair_detail.json", encoding="utf-8") as f:
            for idx, d in enumerate(json.load(f)):
                d['repair_id'] = idx + 1
                db.session.add(RepairDetail(**d))
        db.session.commit()
