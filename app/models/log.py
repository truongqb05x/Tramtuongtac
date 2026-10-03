from app.extensions import db
from datetime import datetime

class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True) # None for system, no ForeignKey to avoid unsigned mismatch
    type = db.Column(db.String(50), nullable=False, default='admin') # 'admin', 'system', 'user'
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    @property
    def user(self):
        if self.user_id:
            from app.models.user import User
            return User.query.get(self.user_id)
        return None

    def to_dict(self):
        actor_name = "Hệ thống"
        u = self.user
        if u:
            actor_name = f"{u.full_name or u.email} ({u.role})"
        
        type_labels = {
            'admin': 'Quản trị',
            'system': 'Hệ thống',
            'user': 'Cảnh báo'
        }
        
        return {
            'id': f"L{self.id:03d}",
            'time': self.created_at.strftime('%H:%M %d/%m/%Y'),
            'actor': actor_name,
            'type': self.type,
            'typeLabel': type_labels.get(self.type, self.type),
            'action': self.action,
            'details': self.details or '',
            'ip': self.ip_address or 'N/A'
        }
