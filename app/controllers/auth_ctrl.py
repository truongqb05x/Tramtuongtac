from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, bcrypt
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_home'))
        
    if request.method == 'POST':
        # Assuming frontend will send JSON for the login API
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid data'}), 400
            
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                return jsonify({'success': False, 'message': 'Tài khoản đã bị khóa.'}), 403
                
            login_user(user, remember=remember)
            return jsonify({'success': True, 'message': 'Đăng nhập thành công', 'redirect_url': url_for('user_home')}), 200
        else:
            return jsonify({'success': False, 'message': 'Email hoặc mật khẩu không chính xác'}), 401
            
    # GET request: render the HTML page
    return render_template('user/auth/login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    terms = data.get('terms', False)
    
    if not terms:
        return jsonify({'success': False, 'message': 'Vui lòng đồng ý với điều khoản.'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email đã tồn tại.'}), 400
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password_hash=hashed_password, full_name=full_name)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Đăng ký thành công.'}), 201

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
