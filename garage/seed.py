import hashlib
import json

from garage import db, app
from garage.models import SystemConfig, Service, SparePart, User, Customer, Employee

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        with open("data/config.json", encoding="utf-8") as f:
            configs = []
            for s in json.load(f):
                config = SystemConfig(**s)
                db.session.add(config)
                configs.append(config)
        db.session.commit()

        with open("data/service.json", encoding="utf-8") as f:
            services = []
            for s in json.load(f):
                service = Service(**s)
                db.session.add(service)
                services.append(service)
        db.session.commit()

        with open("data/spare_parts.json", encoding="utf-8") as f:
            spare_parts = []
            for s in json.load(f):
                spare_part = SparePart(**s)
                db.session.add(spare_part)
                spare_parts.append(spare_part)
        db.session.commit()

        # --- Users ---
        users = []
        with open("data/user.json", encoding="utf-8") as f:
            for u in json.load(f):
                user = User(**u)
                user.password = hashlib.md5(user.password.encode("utf-8")).hexdigest()
                db.session.add(user)
                users.append(user)
        db.session.commit()


        customers = []
        with open("data/customer.json", encoding="utf-8") as f:
            for idx, c in enumerate(json.load(f)):
                c['user_id'] = users[idx % len(users)].id
                cust = Customer(**c)
                db.session.add(cust)
                customers.append(cust)
        db.session.commit()


        employees = []
        with open("data/employee.json", encoding="utf-8") as f:
            for idx, e in enumerate(json.load(f)):
                e['user_id'] = users[(idx + 1) % len(users)].id
                emp = Employee(**e)
                db.session.add(emp)
                employees.append(emp)
        db.session.commit()
