import hashlib
import json

from garage import db, app
from garage.models import SystemConfig, Service, SparePart, User, Customer, Employee


def add_or_update(model, data, key='id'):

    instance = model.query.filter_by(**{key: data[key]}).first() if key in data else None
    if instance:
        for k, v in data.items():
            setattr(instance, k, v)
        return instance, False
    else:
        instance = model(**data)
        db.session.add(instance)
        return instance, True


if __name__ == "__main__":
    with app.app_context():
        db.create_all()


        with open("data/config.json", encoding="utf-8") as f:
            for s in json.load(f):
                add_or_update(SystemConfig, s, key='id')
        db.session.commit()

        with open("data/service.json", encoding="utf-8") as f:
            for s in json.load(f):
                existing = Service.query.filter_by(name=s['name']).first()
                if not existing:
                    service = Service(**s)
                    db.session.add(service)

        db.session.commit()


        with open("data/spare_parts.json", encoding="utf-8") as f:
            for s in json.load(f):
                existing = SparePart.query.filter_by(name=s['name']).first()
                if not existing:
                    spare_part = SparePart(**s)
                    db.session.add(spare_part)
        db.session.commit()


        users = []
        with open("data/user.json", encoding="utf-8") as f:
            user_data_list = json.load(f)
            for u in user_data_list:
                # Dùng username làm key unique
                existing_user = User.query.filter_by(username=u['username']).first()
                if existing_user:
                    users.append(existing_user)
                    continue

                u['password'] = hashlib.md5(u['password'].encode("utf-8")).hexdigest()
                user = User(**u)
                db.session.add(user)
                db.session.flush()
                users.append(user)
        db.session.commit()


        with open("data/customer.json", encoding="utf-8") as f:
            customer_data_list = json.load(f)
            for idx, c in enumerate(customer_data_list):
                existing_cust = Customer.query.filter_by(phone=c['phone']).first()
                if existing_cust:
                    continue

                c['user_id'] = users[idx % len(users)].id
                cust = Customer(**c)
                db.session.add(cust)
        db.session.commit()


        with open("data/employee.json", encoding="utf-8") as f:
            employee_data_list = json.load(f)
            for idx, e in enumerate(employee_data_list):
                existing_emp = Employee.query.filter_by(phone=e['phone']).first()
                if existing_emp:
                    continue

                e['user_id'] = users[(idx + 1) % len(users)].id
                emp = Employee(**e)
                db.session.add(emp)
        db.session.commit()


        print("Tạo thành công dữ liệu ở database!")