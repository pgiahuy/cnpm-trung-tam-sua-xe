import bcrypt
from flask_bcrypt import Bcrypt
from flask import render_template, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from garage import app, dao, db
from garage.models import UserRole, User


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Thiếu username hoặc password"}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()

    if user and Bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(
            identity={
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.user_role
            }
        )
        return jsonify({
            "success": True,
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.user_role
            }
        }), 200
    else:
        return jsonify({
            "success": False,
            "msg": "Sai tên đăng nhập hoặc mật khẩu!"
        }), 401


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({
        "msg": "Đã đăng nhập thành công!",
        "user": current_user
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name', '')
    avatar = data.get('avatar')

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Tên đăng nhập đã tồn tại"}), 400

    dao.add_user(username, full_name, password,avatar)

    return jsonify({"msg": "Tạo tài khoản thành công!"}), 201

if __name__ == '__main__':
    app.run(debug=True)