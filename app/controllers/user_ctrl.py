from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.job import Job

user_bp = Blueprint('user', __name__)

@user_bp.route('/billing/buy-credits')
@login_required
def user_buy_credits():
    return render_template('user/billing/buy_credits.html')

from flask import request, jsonify
from app.extensions import db

@user_bp.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def user_create_job():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        platform = data.get('platform', '').upper()
        action_type = data.get('type', '').upper()
        target_url = data.get('url')
        quantity = int(data.get('slots', 0))
        from decimal import Decimal
        price_per_action = Decimal(str(data.get('reward', 0)))
        total_cost = Decimal(str(data.get('total', 0)))
        
        if current_user.balance < total_cost:
            return jsonify({'success': False, 'message': 'Không đủ Credits'}), 400
            
        # Create job
        new_job = Job(
            user_id=current_user.id,
            platform=platform,
            action_type=action_type,
            target_url=target_url,
            quantity=quantity,
            price_per_action=price_per_action,
            total_cost=total_cost,
            status='RUNNING'
        )
        
        # Deduct balance
        current_user.balance -= total_cost
        
        db.session.add(new_job)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Đã tạo nhiệm vụ thành công',
            'job': new_job.to_dict(),
            'new_balance': current_user.balance
        })

    # GET request
    my_jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.id.desc()).all()
    my_jobs_data = []
    for j in my_jobs:
        d = j.to_dict()
        d['done'] = j.current_count
        d['slots'] = j.quantity
        d['type'] = j.action_type.lower()
        d['platform'] = j.platform.lower()
        d['createdAt'] = j.created_at.strftime('%Y-%m-%d %H:%M:%S')
        d['status'] = 'active' if j.status == 'RUNNING' else ('done' if j.status == 'COMPLETED' else 'paused')
        my_jobs_data.append(d)
        
    return render_template('user/jobs/create_job.html', my_jobs=my_jobs_data)

@user_bp.route('/jobs/<int:job_id>/toggle', methods=['POST'])
@login_required
def user_toggle_job(job_id):
    job = Job.query.filter_by(id=job_id, user_id=current_user.id).first()
    if not job:
        return jsonify({'success': False, 'message': 'Không tìm thấy nhiệm vụ'}), 404
        
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status == 'paused':
        job.status = 'PAUSED'
    elif new_status == 'active':
        job.status = 'RUNNING'
        
    db.session.commit()
    return jsonify({'success': True, 'new_status': new_status})

@user_bp.route('/jobs')
@login_required
def user_job_list():
    from app.models.user import SocialAccount
    has_accounts = SocialAccount.query.filter_by(user_id=current_user.id, is_deleted=False).first() is not None
    # Fetch running jobs that are not deleted
    db_jobs = Job.query.filter_by(status='RUNNING', is_deleted=False).all()
    jobs_data = [job.to_dict() for job in db_jobs]
    return render_template('user/jobs/job_list.html', jobs_data=jobs_data, has_accounts=has_accounts)

@user_bp.route('/api-docs')
def user_api_docs():
    return render_template('user/pages/api_docs.html')

@user_bp.route('/blog')
def user_blog():
    return render_template('user/pages/blog.html')

@user_bp.route('/faq')
def user_faq():
    return render_template('user/pages/faq.html')

@user_bp.route('/privacy')
def user_privacy_policy():
    return render_template('user/pages/privacy_policy.html')

@user_bp.route('/terms')
def user_terms():
    return render_template('user/pages/terms.html')

from flask_bcrypt import check_password_hash, generate_password_hash

@user_bp.route('/settings/account', methods=['GET', 'POST'])
@login_required
def user_settings_account():
    if request.method == 'POST':
        data = request.get_json()
        current_pass = data.get('current_pass')
        new_pass = data.get('new_pass')
        
        if not current_pass or not new_pass:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đủ thông tin.'}), 400
            
        if not check_password_hash(current_user.password, current_pass):
            return jsonify({'success': False, 'message': 'Mật khẩu hiện tại không đúng.'}), 400
            
        if len(new_pass) < 8:
            return jsonify({'success': False, 'message': 'Mật khẩu mới phải có ít nhất 8 ký tự.'}), 400
            
        current_user.password = generate_password_hash(new_pass).decode('utf-8')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công.'})
        
    return render_template('user/settings/account.html')

from app.models.user import SocialAccount

@user_bp.route('/settings/config', methods=['GET', 'POST', 'DELETE'])
@login_required
def user_settings_config():
    if request.method == 'POST':
        data = request.get_json()
        platform = data.get('platform', '').upper()
        url = data.get('url', '')
        if not platform or not url:
            return jsonify({'success': False, 'message': 'Thiếu thông tin'}), 400
            
        # extract social_id (just last part of URL for now)
        social_id = url.rstrip('/').split('/')[-1]
        
        acc = SocialAccount(
            user_id=current_user.id,
            platform=platform,
            profile_url=url,
            social_id=social_id,
            status='ACTIVE'
        )
        db.session.add(acc)
        db.session.commit()
        return jsonify({
            'success': True,
            'account': {
                'id': acc.id,
                'platform': acc.platform.lower(),
                'url': acc.profile_url,
                'name': acc.social_id,
                'verified': acc.status == 'ACTIVE',
                'active': True,
                'addedAt': acc.created_at.strftime('%Y-%m-%d')
            }
        })
        
    elif request.method == 'DELETE':
        data = request.get_json()
        acc_id = data.get('id')
        acc = SocialAccount.query.filter_by(id=acc_id, user_id=current_user.id).first()
        if acc:
            db.session.delete(acc)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Không tìm thấy tài khoản'}), 404

    # GET
    db_accounts = SocialAccount.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(SocialAccount.id.desc()).all()
    accounts_data = []
    for a in db_accounts:
        accounts_data.append({
            'id': a.id,
            'platform': a.platform.lower(),
            'url': a.profile_url,
            'name': a.social_id,
            'verified': a.status == 'ACTIVE',
            'active': False, # just a frontend state
            'addedAt': a.created_at.strftime('%Y-%m-%d')
        })
    if len(accounts_data) > 0:
        accounts_data[0]['active'] = True
        
    return render_template('user/settings/config.html', accounts_data=accounts_data)
