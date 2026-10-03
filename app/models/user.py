from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    role = db.Column(db.Enum('USER', 'ADMIN', name='role_enum'), nullable=False, default='USER')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    social_accounts = db.relationship('SocialAccount', backref='user', lazy='dynamic')

class SocialAccount(db.Model):
    __tablename__ = 'social_accounts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.Enum('FACEBOOK', 'TIKTOK', 'INSTAGRAM', name='platform_enum'), nullable=False)
    social_id = db.Column(db.String(255), nullable=False)
    account_name = db.Column(db.String(255), nullable=True)
    profile_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum('PENDING', 'ACTIVE', 'BLOCKED', name='status_enum'), nullable=False, default='PENDING')
    is_selected = db.Column(db.Boolean, nullable=False, default=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
