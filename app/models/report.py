from app.extensions import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    accused_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    link = db.Column(db.String(500), nullable=True)
    severity = db.Column(db.Enum('high', 'medium', 'low', name='report_severity_enum'), nullable=False, default='medium')
    status = db.Column(db.Enum('pending', 'reviewing', 'resolved', name='report_status_enum'), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
