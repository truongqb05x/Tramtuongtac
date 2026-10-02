from app.extensions import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    social_account_id = db.Column(db.Integer, db.ForeignKey('social_accounts.id'), nullable=False, index=True)
    reward = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    status = db.Column(db.Enum('PENDING', 'VERIFIED', 'REJECTED', name='task_status_enum'), nullable=False, default='PENDING', index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = db.relationship('Job', backref=db.backref('tasks', lazy='dynamic'))
    worker = db.relationship('User', foreign_keys=[worker_id], backref=db.backref('tasks', lazy='dynamic'))
    social_account = db.relationship('SocialAccount', backref=db.backref('tasks', lazy='dynamic'))
