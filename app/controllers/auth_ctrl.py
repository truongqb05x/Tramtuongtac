from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, bcrypt
from app.models.user import User
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

auth_bp = Blueprint('auth', __name__)

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = [
    "openid", 
    "https://www.googleapis.com/auth/userinfo.email", 
    "https://www.googleapis.com/auth/userinfo.profile"
]

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
    return redirect('/')

@auth_bp.route('/google/login')
def google_login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        scopes=SCOPES, 
        redirect_uri=url_for("auth.google_callback", _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@auth_bp.route('/google/callback')
def google_callback():
    state = session.get('state')
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        scopes=SCOPES, 
        state=state,
        redirect_uri=url_for("auth.google_callback", _external=True)
    )
    
    # Fetch token
    flow.fetch_token(authorization_response=request.url)
    
    # Get user info
    credentials = flow.credentials
    request_session = google_requests.Request()
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=request_session,
        audience=credentials.client_id,
        clock_skew_in_seconds=300
    )
    
    email = id_info.get("email")
    name = id_info.get("name")
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        if not user.is_active:
            flash("Tài khoản đã bị khóa.", "error")
            return redirect(url_for('auth.login'))
        login_user(user)
    else:
        # Create a new user
        random_password = bcrypt.generate_password_hash(os.urandom(24)).decode('utf-8')
        user = User(email=email, full_name=name, password_hash=random_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        
    return redirect(url_for('user_home'))
