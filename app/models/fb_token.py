from app.extensions import db
from datetime import datetime

class FbToken(db.Model):
    __tablename__ = 'fb_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(1000), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
