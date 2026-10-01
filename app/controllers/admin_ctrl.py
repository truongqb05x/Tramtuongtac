from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from flask_login import login_required, current_user
from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ADMIN':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

from app.models.user import User
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.task import Task
from app.extensions import db
from sqlalchemy import func

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    # KPI Grid
    user_count = User.query.count()
    job_count = Job.query.count()
    
    # Recent Tasks (Jobs)
    recent_jobs = Job.query.order_by(Job.id.desc()).limit(5).all()
    recent_jobs_data = []
    for j in recent_jobs:
        user = User.query.get(j.user_id)
        recent_jobs_data.append({
            'id': f'#J-{j.id}',
            'creator': user.full_name if user else 'Unknown',
            'platform': j.platform,
            'req': j.action_type,
            'reward': f'{int(j.price_per_action)} Credits',
            'status': j.status.lower(),
            'statusLabel': 'Đang chạy' if j.status == 'RUNNING' else ('Hoàn thành' if j.status == 'COMPLETED' else 'Đã hủy')
        })
        
    # Recent Transactions
    recent_txs = Transaction.query.order_by(Transaction.id.desc()).limit(5).all()
    recent_txs_data = []
    for tx in recent_txs:
        user = User.query.get(tx.user_id)
        recent_txs_data.append({
            'id': f'#TX-{tx.id}',
            'user': user.full_name if user else 'Unknown',
            'amount': f'{int(tx.amount)} VND',
            'credits': f'+{int(tx.amount/10)}', # assuming 10 VND = 1 Credit
            'time': tx.created_at.strftime('%d/%m/%Y'),
            'status': 'ok' if tx.status == 'SUCCESS' else ('warn' if tx.status == 'PENDING' else 'danger'),
            'statusLabel': 'Thành công' if tx.status == 'SUCCESS' else ('Chờ xử lý' if tx.status == 'PENDING' else 'Thất bại')
        })

    # Statistics per platform
    platforms = ['FACEBOOK', 'TIKTOK', 'INSTAGRAM']
    stats_data = []
    for plat in platforms:
        plat_jobs = Job.query.filter_by(platform=plat).all()
        total_jobs = len(plat_jobs)
        running = len([j for j in plat_jobs if j.status == 'RUNNING'])
        total_reward = sum([j.total_cost for j in plat_jobs])
        total_fee = total_reward * 0.02 # Assuming 2% fee for now
        stats_data.append({
            'platform': plat.capitalize(),
            'active': str(running),
            'total': str(total_jobs),
            'reward': str(int(total_reward)),
            'fee': str(int(total_fee)),
            'status': 'ok' if total_jobs > 0 else 'mute',
            'statusLabel': 'Ổn định' if total_jobs > 0 else 'Chưa có'
        })
        
    return render_template('admin/Admin.html', 
        user_count=user_count, 
        job_count=job_count,
        recent_jobs_data=recent_jobs_data,
        recent_txs_data=recent_txs_data,
        stats_data=stats_data
    )

@admin_bp.route('/tasks')
def admin_tasks():
    return render_template('admin/tasks.html')

@admin_bp.route('/transactions')
@login_required
@admin_required
def admin_transactions():
    txs = Transaction.query.order_by(Transaction.id.desc()).all()
    txs_data = []
    for tx in txs:
        u = User.query.get(tx.user_id)
        txs_data.append({
            'id': f'#TX-{tx.id}',
            'user': u.full_name or 'N/A',
            'method': tx.type,
            'amount': f'{int(tx.amount):,} VND',
            'credits': f'+{int(tx.amount/10):,}',
            'time': tx.created_at.strftime('%d/%m/%Y %H:%M'),
            'status': 'ok' if tx.status == 'SUCCESS' else ('warn' if tx.status == 'PENDING' else 'danger'),
            'statusLabel': 'Thành công' if tx.status == 'SUCCESS' else ('Chờ xử lý' if tx.status == 'PENDING' else 'Thất bại')
        })
    return render_template('admin/transactions.html', txs_data=txs_data)

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    users_data = []
    for u in users:
        # Assuming we can count active jobs per user
        active_jobs = Job.query.filter_by(user_id=u.id, status='RUNNING').count()
        users_data.append({
            'id': f'#{u.id}',
            'name': u.full_name or 'N/A',
            'email': u.email,
            'role': u.role,
            'balance': f"{int(u.balance):,}",
            'status': 'active' if u.is_active else 'banned',
            'statusLabel': 'Hoạt động' if u.is_active else 'Bị khóa',
            'joinDate': u.created_at.strftime('%d/%m/%Y'),
            'activeJobs': active_jobs
        })
    return render_template('admin/users.html', users_data=users_data)

@admin_bp.route('/reports')
@login_required
@admin_required
def admin_reports():
    # Reports table doesn't exist yet, passing empty data
    reports_data = []
    return render_template('admin/reports.html', reports_data=reports_data)

from app.models.user import SocialAccount

@admin_bp.route('/user-config')
@login_required
@admin_required
def admin_user_config():
    accounts = SocialAccount.query.order_by(SocialAccount.id.desc()).all()
    accounts_data = []
    for a in accounts:
        u = User.query.get(a.user_id)
        accounts_data.append({
            'id': f'A-{a.id}',
            'owner': u.full_name or 'N/A',
            'email': u.email,
            'platform': a.platform.capitalize(),
            'linkedName': a.social_id,
            'link': a.profile_url or '#',
            'sysCheck': 'Bình thường',
            'sysCode': 'ok',
            'status': a.status.lower(),
            'statusLabel': 'Chờ duyệt' if a.status == 'PENDING' else ('Đã duyệt' if a.status == 'ACTIVE' else 'Bị khóa')
        })
    return render_template('admin/user_config.html', accounts_data=accounts_data)

@admin_bp.route('/config')
def admin_config():
    return render_template('admin/config.html')

@admin_bp.route('/logs')
def admin_logs():
    return render_template('admin/logs.html')

@admin_bp.route('/stats')
@login_required
@admin_required
def admin_stats():
    total_txs = Transaction.query.filter_by(status='SUCCESS', type='DEPOSIT').all()
    total_revenue = sum([tx.amount for tx in total_txs])
    
    total_jobs = Job.query.all()
    total_reward = sum([j.total_cost for j in total_jobs])
    total_fee = total_reward * 0.02
    
    user_count = User.query.count()
    completed_tasks = Task.query.filter_by(status='VERIFIED').count()
    
    # Calculate top users
    users = User.query.all()
    top_users = []
    for u in users:
        u_txs = Transaction.query.filter_by(user_id=u.id, status='SUCCESS', type='DEPOSIT').all()
        u_revenue = sum([t.amount for t in u_txs])
        u_jobs = Job.query.filter_by(user_id=u.id).all()
        u_spent = sum([j.total_cost for j in u_jobs])
        if u_revenue > 0 or u_spent > 0:
            top_users.append({
                'name': u.full_name or 'N/A',
                'email': u.email,
                'initials': (u.full_name or 'U')[0].upper(),
                'revenue': f"{int(u_revenue):,}",
                'spent': f"{int(u_spent):,}"
            })
    top_users.sort(key=lambda x: int(x['revenue'].replace(',', '')), reverse=True)
    top_users = top_users[:5]
    
    # Platform stats
    p_fb = Job.query.filter_by(platform='FACEBOOK').count()
    p_tt = Job.query.filter_by(platform='TIKTOK').count()
    p_ig = Job.query.filter_by(platform='INSTAGRAM').count()
    total_j = p_fb + p_tt + p_ig
    if total_j == 0: total_j = 1 # prevent div by zero
    plat_stats = {
        'fb': int((p_fb / total_j) * 100),
        'tt': int((p_tt / total_j) * 100),
        'ig': int((p_ig / total_j) * 100)
    }

    return render_template('admin/stats.html',
        total_revenue=f"{int(total_revenue):,}",
        total_fee=f"{int(total_fee):,}",
        user_count=f"{user_count:,}",
        completed_tasks=f"{completed_tasks:,}",
        top_users=top_users,
        plat_stats=plat_stats
    )
