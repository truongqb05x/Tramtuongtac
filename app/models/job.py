from app.extensions import db
from datetime import datetime

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.Enum('FACEBOOK', 'TIKTOK', 'INSTAGRAM', name='job_platform_enum'), nullable=False)
    action_type = db.Column(db.Enum('LIKE', 'FOLLOW', 'COMMENT', 'SHARE', name='action_type_enum'), nullable=False)
    target_url = db.Column(db.String(1000), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    current_count = db.Column(db.Integer, nullable=False, default=0)
    price_per_action = db.Column(db.Numeric(15, 2), nullable=False)
    total_cost = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum('RUNNING', 'COMPLETED', 'CANCELED', 'PAUSED', name='job_status_enum'), nullable=False, default='RUNNING')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('jobs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'mark': self.platform[:2].upper() if self.platform else '',
            'category': self.action_type,
            'title': f'Tạo bởi {self.user.full_name or self.user.email if self.user else "Khách"}',
            'reward': float(self.price_per_action),
            'duration': 'Tùy chọn',
            'verify': 'Tự động',
            'slots': f'{self.current_count} / {self.quantity} suất',
            'trust': 100, # Mocked trust score
            'creator': self.user.full_name or self.user.email if self.user else "Khách",
            'status': 'Available',
            'statusType': 'ok',
            'desc': f'Link: {self.target_url}'
        }
