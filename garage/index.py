
from flask import render_template, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from garage import app, dao, db, bcrypt
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

    if user and dao.auth_user(username, password):
        access_token = create_access_token(
            identity={
                "id": user.id,
                "username": user.username,
                "full_name": user.name,
                "user_role": user.user_role.name
            }
        )
        return jsonify({
            "success": True,
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.name,
                "user_role": user.user_role.name
            }
        }), 200
    else:
        return jsonify({
            "success": False,
            "msg": "Sai tên đăng nhập hoặc mật khẩu!",
        }), 401

@app.route('/api/logout', methods=['POST'])

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({
        "msg": "Đã đăng nhập thành công!",
        "user": current_user
    })


@app.route('/api/register', methods=['POST'])
def register_public():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Dữ liệu không hợp lệ"}), 400

    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name', '').strip()
    avatar = data.get('avatar', 'default.jpg')

    if not username or not password:
        return jsonify({"msg": "Vui lòng nhập tài khoản và mật khẩu"}), 400

    if User.query.filter(
        (User.username == username)
    ).first():
        return jsonify({"msg": "Số điện thoại đã được sử dụng"}), 400

    try:
        dao.add_user(
            name=full_name or username,
            username=username,
            password=password,
            avatar=avatar,
        )

        return jsonify({
            "success": True,
            "msg": "Đăng ký thành công! Bạn có thể đăng nhập ngay.",
            "redirect": "/login"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Đăng ký thất bại, vui lòng thử lại!"}), 500

if __name__ == '__main__':
    app.run(debug=True)