from flask import Blueprint, render_template, jsonify, request
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
from app.models.user import User
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.task import Task
from app.extensions import db
from sqlalchemy import func
import json
from app.models.user import SocialAccount
from app.services.platform_cfg import load_platforms, save_platforms
from app.services.system_cfg import load_system_config, save_system_config, update_system_field
from app.models.log import ActionLog
from app.extensions import db
from app.models.fb_token import FbToken
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ADMIN':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    # KPI Grid
    user_count = db.session.query(func.count(User.id)).scalar() or 0
    job_count = db.session.query(func.count(Job.id)).scalar() or 0
    circulating_credits = db.session.query(func.sum(User.balance)).scalar() or 0

    job_stats = db.session.query(Job.status, func.count(Job.id), func.sum(Job.total_cost)).group_by(Job.status).all()
    running_jobs = 0
    completed_jobs = 0
    total_cost_all = 0
    for status, count, cost in job_stats:
        if status == 'RUNNING':
            running_jobs += count
        elif status == 'COMPLETED':
            completed_jobs += count
        total_cost_all += float(cost or 0)
        
    completion_rate = round((completed_jobs / job_count * 100), 1) if job_count > 0 else 0
    revenue = total_cost_all * 0.02 # 2% fee

    def format_num(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(int(n))

    kpi = {
        'users': format_num(user_count),
        'jobs': format_num(job_count),
        'completion_rate': f"{completion_rate}%",
        'credits': format_num(circulating_credits),
        'revenue': format_num(revenue),
        'running_jobs': format_num(running_jobs)
    }
    
    # Recent Tasks (Jobs)
    recent_jobs = Job.query.order_by(Job.id.desc()).limit(5).all()
    recent_jobs_data = []
    for j in recent_jobs:
        user = User.query.get(j.user_id)
        cat_map = {
            'LIKE': 'Tương tác (Like)',
            'LOVE': 'Tương tác (Tym)',
            'WOW': 'Tương tác (Wow)',
            'HAHA': 'Tương tác (Haha)',
            'SAD': 'Tương tác (Buồn)',
            'FOLLOW': 'Theo dõi',
            'COMMENT': 'Bình luận',
            'SHARE': 'Chia sẻ'
        }
        action_type_str = j.action_type.name if hasattr(j.action_type, 'name') else str(j.action_type)
        
        recent_jobs_data.append({
            'id': f'#J-{j.id}',
            'creator': user.full_name if user else 'Unknown',
            'platform': j.platform,
            'req': cat_map.get(action_type_str, action_type_str),
            'reward': f'{float(j.price_per_action or 0):g} Credits',
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
            'credits': f'+{int(float(tx.amount)/10)}', # assuming 10 VND = 1 Credit
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
        total_reward = sum([float(j.total_cost) for j in plat_jobs])
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
        
    return render_template('admin/dashboard.html', 
        kpi=kpi,
        recent_jobs_data=recent_jobs_data,
        recent_txs_data=recent_txs_data,
        stats_data=stats_data
    )

@admin_bp.route('/tasks')
@login_required
@admin_required
def admin_tasks():
    jobs = Job.query.order_by(Job.id.desc()).all()
    tasks_data = []
    for j in jobs:
        user = j.user
        status = j.status.lower()
        if status == 'running':
            status_label = 'Đang chạy'
            st_cls = 'running'
        elif status == 'completed':
            status_label = 'Hoàn thành'
            st_cls = 'completed'
        elif status == 'canceled':
            status_label = 'Đã hủy'
            st_cls = 'rejected'
        else:
            status_label = status
            st_cls = 'pending'

        cat_map = {
            'LIKE': 'Tương tác (Like)',
            'LOVE': 'Tương tác (Tym)',
            'WOW': 'Tương tác (Wow)',
            'HAHA': 'Tương tác (Haha)',
            'SAD': 'Tương tác (Buồn)',
            'FOLLOW': 'Theo dõi',
            'COMMENT': 'Bình luận',
            'SHARE': 'Chia sẻ'
        }
        
        action_type_str = j.action_type.name if hasattr(j.action_type, 'name') else str(j.action_type)
        tasks_data.append({
            'raw_id': j.id,
            'id': f'#J-{j.id}',
            'creator': user.full_name if user else 'Unknown',
            'handle': user.email if user else '',
            'platform': j.platform.capitalize(),
            'req': cat_map.get(action_type_str, action_type_str),
            'reward': str(float(j.price_per_action)) if j.price_per_action else "0",
            'qty': str(j.quantity),
            'total_cost': str(float(j.total_cost)) if j.total_cost else "0",
            'status': st_cls,
            'statusLabel': status_label
        })
    return render_template('admin/tasks.html', tasks_data=json.dumps(tasks_data))

@admin_bp.route('/api/jobs/<int:job_id>/cancel', methods=['POST'])
@login_required
@admin_required
def admin_cancel_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.status == 'CANCELED':
        return jsonify({'success': False, 'message': 'Nhiệm vụ đã bị hủy trước đó.'})
        
    job.status = 'CANCELED'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã hủy nhiệm vụ.'})

@admin_bp.route('/api/jobs/<int:job_id>/restore', methods=['POST'])
@login_required
@admin_required
def admin_restore_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.status != 'CANCELED':
        return jsonify({'success': False, 'message': 'Chỉ có thể khôi phục nhiệm vụ đã hủy.'})
        
    job.status = 'RUNNING'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã khôi phục nhiệm vụ.'})

@admin_bp.route('/api/jobs/<int:job_id>/complete', methods=['POST'])
@login_required
@admin_required
def admin_complete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.status == 'COMPLETED':
        return jsonify({'success': False, 'message': 'Nhiệm vụ đã hoàn thành trước đó.'})
        
    job.status = 'COMPLETED'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã hoàn thành nhiệm vụ.'})

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

@admin_bp.route('/user-config')
@login_required
@admin_required
def admin_user_config():
    accounts = SocialAccount.query.order_by(SocialAccount.id.desc()).all()
    accounts_data = []
    for a in accounts:
        u = User.query.get(a.user_id)
        accounts_data.append({
            'raw_id': a.id,
            'id': f'A-{a.id}',
            'owner': u.full_name or 'N/A',
            'email': u.email,
            'platform': a.platform.capitalize(),
            'linkedName': a.social_id,
            'link': a.profile_url or '#',
            'sysCheck': 'Bình thường',
            'sysCode': 'ok',
            'status': 'blocked' if a.status == 'BLOCKED' else a.status.lower(),
            'statusLabel': 'Chờ duyệt' if a.status == 'PENDING' else ('Đã duyệt' if a.status == 'ACTIVE' else 'Đã bị vô hiệu hóa')
        })
    return render_template('admin/user_config.html', accounts_data=accounts_data)

@admin_bp.route('/api/social-accounts/<int:account_id>/block', methods=['POST'])
@login_required
@admin_required
def admin_block_account(account_id):
    account = SocialAccount.query.get_or_404(account_id)
    if account.status == 'BLOCKED':
        return jsonify({'success': False, 'message': 'Tài khoản đã bị vô hiệu hóa trước đó.'}), 400
        
    account.status = 'BLOCKED'
    account.is_selected = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã vô hiệu hóa tài khoản liên kết.'})

@admin_bp.route('/api/social-accounts/<int:account_id>/approve', methods=['POST'])
@login_required
@admin_required
def admin_approve_account(account_id):
    account = SocialAccount.query.get_or_404(account_id)
    if account.status == 'ACTIVE':
        return jsonify({'success': False, 'message': 'Tài khoản đã được duyệt trước đó.'}), 400
        
    account.status = 'ACTIVE'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã duyệt tài khoản liên kết.'})

@admin_bp.route('/config')
@login_required
@admin_required
def admin_config():
    platforms = load_platforms()
    system_config = load_system_config()
    active_tokens = FbToken.query.filter_by(is_active=True).all()
    token_count = len(active_tokens)
    return render_template('admin/config.html', platforms=platforms, system_config=system_config, token_count=token_count)

@admin_bp.route('/api/platforms', methods=['POST'])
@login_required
@admin_required
def api_save_platforms():
    data = request.get_json()
    save_platforms(data)
    return jsonify({'success': True})

@admin_bp.route('/api/system', methods=['POST'])
@login_required
@admin_required
def api_save_system():
    data = request.get_json()
    save_system_config(data)
    return jsonify({'success': True})

@admin_bp.route('/api/system/field', methods=['POST'])
@login_required
@admin_required
def api_save_system_field():
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')
    if not key:
        return jsonify({'success': False, 'message': 'Thiếu key'}), 400
    update_system_field(key, value)
    
    log = ActionLog(
        user_id=current_user.id,
        type='admin',
        action=f'Cập nhật cấu hình: {key}',
        details=f'Giá trị mới: {value}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/logs')
@login_required
@admin_required
def admin_logs():
    logs = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(100).all()
    logs_data = [l.to_dict() for l in logs]
    return render_template('admin/logs.html', logs_data=logs_data)

@admin_bp.route('/stats')
@login_required
@admin_required
def admin_stats():
    total_txs = Transaction.query.filter_by(status='SUCCESS', type='DEPOSIT').all()
    total_revenue = sum([float(tx.amount) for tx in total_txs])
    sys_cfg = load_system_config()
    fee_rate = float(sys_cfg.get('platform_fee', 10)) / 100.0

    total_jobs = Job.query.all()
    total_reward = sum([float(j.total_cost) for j in total_jobs])
    total_fee = total_reward * fee_rate
    
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

@admin_bp.route('/api/tokens', methods=['GET', 'POST'])
@login_required
def api_tokens():
    if current_user.role != 'ADMIN':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    if request.method == 'GET':
        tokens = FbToken.query.filter_by(is_active=True).all()
        return jsonify({'success': True, 'tokens': [t.token for t in tokens]})
        
    elif request.method == 'POST':
        data = request.get_json()
        token_list = data.get('tokens', [])
        
        try:
            # Clear all current active tokens
            FbToken.query.filter_by(is_active=True).update({'is_active': False})
            
            # Insert new ones
            for t in token_list:
                t_str = t.strip()
                if t_str:
                    new_token = FbToken(token=t_str, is_active=True)
                    db.session.add(new_token)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Đã lưu danh sách Token'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
