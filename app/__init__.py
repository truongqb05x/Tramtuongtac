from flask import Flask, render_template
from app.extensions import db, bcrypt, login_manager
from dotenv import load_dotenv
import os
from app.controllers.auth_ctrl import auth_bp
from app.controllers.user_ctrl import user_bp
from app.controllers.admin_ctrl import admin_bp
from flask import request
from flask_login import current_user
from app.services.system_cfg import load_system_config
from flask import redirect, url_for
from app.models.job import Job
from app.models.user import SocialAccount
from app.models.task import Task
from flask_login import login_required
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
        
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)    
    @app.before_request
    def check_maintenance():
        if request.path.startswith('/static') or request.path.startswith('/admin'):
            return
            
        config = load_system_config()
        if config.get('maintenance_mode', False):
            if current_user.is_authenticated and current_user.role == 'ADMIN':
                return
            # Chỉ cho phép các đường dẫn liên quan đến việc Đăng nhập để Admin có thể login
            if request.path in ['/auth/login', '/auth/api/login', '/login']:
                return
            return render_template('user/errors/503.html'), 503

    # We will temporarily keep the root routes here to avoid breaking everything at once
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('user_home'))
        return render_template('user/index.html')
    @app.route('/home')
    @login_required
    def user_home():
        open_jobs_count = Job.query.filter_by(status='RUNNING', is_deleted=False).count()
        has_accounts = SocialAccount.query.filter_by(user_id=current_user.id, is_deleted=False).first() is not None
        has_done_task = Task.query.filter_by(worker_id=current_user.id).first() is not None
        has_created_job = Job.query.filter_by(user_id=current_user.id).first() is not None
        return render_template('user/home.html', open_jobs_count=open_jobs_count, has_accounts=has_accounts, has_done_task=has_done_task, has_created_job=has_created_job)
        
    from flask import redirect, url_for
    @app.route('/login')
    def user_login():
        return redirect(url_for('auth.login'))
        
    @app.route('/register')
    def user_register():
        # Because we only have /auth/login rendering the html in auth_bp and switching via JS hash or we can just redirect to login
        return redirect(url_for('auth.login', _anchor='register'))
        
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('user/errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('user/errors/500.html'), 500
        
    return app
