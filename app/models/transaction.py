from app.extensions import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    type = db.Column(db.Enum('DEPOSIT', 'WITHDRAW', 'CREATE_JOB', 'TASK_REWARD', 'REFUND', name='transaction_type_enum'), nullable=False)
    status = db.Column(db.Enum('PENDING', 'SUCCESS', 'FAILED', name='transaction_status_enum'), nullable=False, default='PENDING')
    reference_code = db.Column(db.String(255), unique=True, nullable=True)
    description = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
