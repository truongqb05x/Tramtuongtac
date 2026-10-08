import json
import re
import time
import urllib.parse
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
import requests
from flask import Blueprint, jsonify, render_template, request, session
from flask_bcrypt import check_password_hash, generate_password_hash
from flask_login import current_user, login_required
from sqlalchemy import or_
from app.extensions import db
from app.models.job import Job
from app.models.task import Task
from app.models.transaction import Transaction
from app.models.user import SocialAccount, User
from app.services.facebook import check_fb_action_status, get_facebook_profile, verify_fb_post_id
from app.services.platform_cfg import load_platforms
from app.services.system_cfg import load_system_config


user_bp = Blueprint('user', __name__)

@user_bp.route('/tools/get-id')
@login_required
def tools_get_id():
    return render_template('user/tools/get_id.html')

@user_bp.route('/donate')
def user_donate():
    return render_template('user/pages/donate.html')

@user_bp.route('/billing/buy-credits')
@login_required
def user_buy_credits():
    return render_template('user/billing/buy_credits.html')

@user_bp.route('/billing/transfer-credits')
@login_required
def user_transfer_credits():
    
    # Get transfer history for this user
    # A transaction where type is TRANSFER_OUT (user sent to someone) or TRANSFER_IN (user received from someone)
    db_history = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type.in_(['TRANSFER_IN', 'TRANSFER_OUT'])
    ).order_by(Transaction.id.desc()).limit(5).all()
    
    history_data = []
    # We need to know who the other party was. We can parse it from description or add a column.
    # To keep schema changes minimal, let's parse from description which can be "Chuyển tiền cho abc@xyz.com"
    for tx in db_history:
        other_email = "Unknown"
        match = re.search(r'([\w\.-]+@[\w\.-]+)', tx.description or '')
        if match:
            other_email = match.group(1)
            
        history_data.append({
            'id': f'TX-{tx.id}',
            'type': 'out' if tx.type == 'TRANSFER_OUT' else 'in',
            'user': {'email': other_email},
            'amount': float(tx.amount),
            'note': tx.description,
            'time': tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ts': int(tx.created_at.timestamp() * 1000)
        })
    
    return render_template('user/billing/transfer_credits.html', history_data_json=json.dumps(history_data))

@user_bp.route('/api/users/search')
@login_required
def api_search_users():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': True, 'data': []})
    
    # Don't show current user in search results
    users = User.query.filter(
        User.email.ilike(f'%{query}%'),
        User.id != current_user.id
    ).limit(6).all()
    
    results = [{'id': u.id, 'email': u.email} for u in users]
    return jsonify({'success': True, 'data': results})

@user_bp.route('/api/transfer', methods=['POST'])
@login_required
def api_transfer_credits():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Thiếu dữ liệu'}), 400
        
    recipient_id = data.get('recipient_id')
    amount = data.get('amount')
    
    if not recipient_id or not amount:
        return jsonify({'success': False, 'message': 'Thiếu thông tin người nhận hoặc số tiền'}), 400
        
    try:
        amount = int(amount)
        recipient_id = int(recipient_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Số tiền hoặc ID không hợp lệ'}), 400
        
    if amount < 50:
        return jsonify({'success': False, 'message': 'Số lượng tối thiểu là 50 Credits'}), 400
        
    if current_user.balance < amount:
        return jsonify({'success': False, 'message': 'Số dư không đủ'}), 400
    
    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'success': False, 'message': 'Không tìm thấy người nhận'}), 404
        
    try:
        # Deduct from sender
        current_user.balance -= amount
        tx_out = Transaction(
            user_id=current_user.id,
            amount=amount,
            type='TRANSFER_OUT',
            status='SUCCESS',
            description=f'Chuyển tiền cho {recipient.email}'
        )
        db.session.add(tx_out)
        
        # Add to receiver
        recipient.balance += amount
        tx_in = Transaction(
            user_id=recipient.id,
            amount=amount,
            type='TRANSFER_IN',
            status='SUCCESS',
            description=f'Nhận tiền từ {current_user.email}'
        )
        db.session.add(tx_in)
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Giao dịch thành công!',
            'new_balance': current_user.balance
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Lỗi hệ thống khi chuyển tiền: ' + str(e)}), 500

@user_bp.route('/jobs/create', methods=['GET', 'POST'])
@login_required
def user_create_job():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        platform = data.get('platform', '').upper()
        raw_type = data.get('type', '').upper()
        action_type = raw_type.split('_')[-1] if '_' in raw_type else raw_type
        if action_type == 'HEART': action_type = 'LIKE'
        if action_type == 'SUB': action_type = 'FOLLOW'
        target_url = data.get('url')
        quantity = int(data.get('slots', 0))
        price_per_action = Decimal(str(data.get('reward', 0)))
        total_cost = Decimal(str(data.get('total', 0)))
        
        if quantity < 5:
            return jsonify({'success': False, 'message': 'Số lượng tối thiểu phải từ 5 trở lên'}), 400
            
        if current_user.balance < total_cost:
            return jsonify({'success': False, 'message': 'Không đủ Credits'}), 400
            
        config = load_system_config()
        initial_status = 'PAUSED' if config.get('safe_mode', False) else 'RUNNING'

        # Create job
        new_job = Job(
            user_id=current_user.id,
            platform=platform,
            action_type=action_type,
            target_url=target_url,
            quantity=quantity,
            price_per_action=price_per_action,
            total_cost=total_cost,
            status=initial_status
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
        d['url'] = j.target_url
        d['createdAt'] = j.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if j.status == 'RUNNING':
            d['status'] = 'active'
        elif j.status == 'COMPLETED':
            d['status'] = 'done'
        elif j.status == 'CANCELED':
            d['status'] = 'canceled'
        else:
            d['status'] = 'paused'
        my_jobs_data.append(d)
        
    system_config = load_system_config()
    return render_template('user/jobs/create_job.html', my_jobs=my_jobs_data, system_config=system_config)

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
    system_config = load_system_config()
    daily_limit = system_config.get('daily_task_limit', 200)
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = Task.query.filter(Task.worker_id == current_user.id, Task.created_at >= today_start).count()
    if completed_today >= daily_limit:
        return f'Bạn đã đạt giới hạn {daily_limit} nhiệm vụ/ngày. Vui lòng quay lại vào ngày mai!', 403

    now = time.time()
    last_get = session.get('last_get_jobs', 0)
    if now - last_get < 15:
        return f'Vui lòng đợi {int(15 - (now - last_get))}s trước khi tải lại danh sách nhiệm vụ. Vui lòng quay lại.', 429
    session['last_get_jobs'] = now
    session.modified = True

    has_accounts = SocialAccount.query.filter_by(user_id=current_user.id, is_deleted=False).first() is not None
    # Fetch running jobs that are not deleted
    db_jobs = Job.query.filter_by(status='RUNNING', is_deleted=False).all()
    
    active_accs = SocialAccount.query.filter_by(user_id=current_user.id, is_selected=True, is_deleted=False).all()
    completed_targets = {}
    for acc in active_accs:
        completed_targets[acc.platform] = set()
        tasks = Task.query.filter_by(social_account_id=acc.id).all()
        for t in tasks:
            if t.job:
                completed_targets[acc.platform].add((t.job.target_url, t.job.action_type))
                
    filtered_jobs = []
    seen_targets = set()
    for job in db_jobs:
        if job.platform in completed_targets:
            if (job.target_url, job.action_type) in completed_targets[job.platform]:
                continue
        
        # Avoid showing duplicate jobs for the same target_url and action_type
        # so the user doesn't see 5 identical jobs
        target_key = (job.platform, job.target_url, job.action_type)
        if target_key in seen_targets:
            continue
        seen_targets.add(target_key)
        
        filtered_jobs.append(job)

    # Sắp xếp: ưu tiên job có current_count thấp hơn (tiến trình ít hơn)
    # Nếu cùng current_count thì ưu tiên job được tạo muộn hơn (created_at lớn hơn)
    filtered_jobs.sort(key=lambda j: (j.current_count, -(j.created_at.timestamp() if j.created_at else 0)))

    jobs_data = [job.to_dict() for job in filtered_jobs]
    system_config = load_system_config()
    return render_template('user/jobs/job_list.html', jobs_data=jobs_data, has_accounts=has_accounts, system_config=system_config)

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

@user_bp.route('/settings/account', methods=['GET', 'POST'])
@login_required
def user_settings_account():
    if request.method == 'POST':
        data = request.get_json()
        current_pass = data.get('current_pass')
        new_pass = data.get('new_pass')
        
        if not current_pass or not new_pass:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đủ thông tin.'}), 400
            
        if not check_password_hash(current_user.password_hash, current_pass):
            return jsonify({'success': False, 'message': 'Mật khẩu hiện tại không đúng.'}), 400
            
        if len(new_pass) < 6:
            return jsonify({'success': False, 'message': 'Mật khẩu mới phải có ít nhất 6 ký tự.'}), 400
            
        current_user.password_hash = generate_password_hash(new_pass).decode('utf-8')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công.'})
        
    return render_template('user/settings/account.html')


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
        parsed_url = urllib.parse.urlparse(url)
        if 'profile.php' in parsed_url.path:
            qs = urllib.parse.parse_qs(parsed_url.query)
            if 'id' in qs:
                social_id = qs['id'][0]
        else:
            match = re.search(r'/(\d+)/?$', parsed_url.path)
            if match:
                social_id = match.group(1)
        
        account_name = None
        if platform == 'FACEBOOK':
            fb_info = get_facebook_profile(url)
            account_name = fb_info.get('name')
        config = load_system_config()
        is_safe_mode = config.get('safe_mode', False)
        initial_status = 'PENDING' if is_safe_mode else 'ACTIVE'

        # Check if user has other accounts for this platform
        has_other = SocialAccount.query.filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == platform,
            SocialAccount.social_id != social_id
        ).first()
        is_first = (has_other is None)

        # Check if it already exists
        existing_acc = SocialAccount.query.filter_by(platform=platform, social_id=social_id).first()
        if existing_acc:
            existing_acc.user_id = current_user.id
            existing_acc.profile_url = url
            existing_acc.account_name = account_name
            existing_acc.status = initial_status
            existing_acc.is_selected = is_first
            existing_acc.is_deleted = False
            acc = existing_acc
        else:
            acc = SocialAccount(
                user_id=current_user.id,
                platform=platform,
                profile_url=url,
                social_id=social_id,
                account_name=account_name,
                status=initial_status,
                is_selected=is_first
            )
            db.session.add(acc)
        db.session.commit()
        return jsonify({
            'success': True,
            'account': {
                'id': acc.id,
                'platform': acc.platform.lower(),
                'url': acc.profile_url,
                'name': acc.account_name if acc.account_name else acc.social_id,
                'verified': not is_safe_mode,
                'status': initial_status.lower(),
                'active': acc.is_selected,
                'addedAt': acc.created_at.strftime('%Y-%m-%d')
            }
        })
        
    elif request.method == 'DELETE':
        data = request.get_json()
        acc_id = data.get('id')
        acc = SocialAccount.query.filter_by(id=acc_id, user_id=current_user.id).first()
        if acc:
            acc.is_deleted = True
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
            'name': a.account_name if a.account_name else a.social_id,
            'verified': a.status == 'ACTIVE',
            'status': a.status.lower(),
            'active': a.is_selected,
            'addedAt': a.created_at.strftime('%Y-%m-%d')
        })
        
    active_platforms = [p for p in load_platforms() if p.get('active')]
    return render_template('user/settings/config.html', accounts_data=accounts_data, platforms=active_platforms)

@user_bp.route('/settings/config/select', methods=['POST'])
@login_required
def user_settings_config_select():
    data = request.get_json()
    acc_id = data.get('id')
    
    acc = SocialAccount.query.filter_by(id=acc_id, user_id=current_user.id).first()
    if not acc:
        return jsonify({'success': False, 'message': 'Không tìm thấy tài khoản'}), 404
        
    if acc.status == 'BLOCKED':
        return jsonify({'success': False, 'message': 'Tài khoản đã bị vô hiệu hóa'}), 400
        
    # Deselect all other accounts of this user
    SocialAccount.query.filter_by(user_id=current_user.id).update({'is_selected': False})
    
    # Select this account
    acc.is_selected = True
    db.session.commit()
    
    return jsonify({'success': True})

@user_bp.route('/api/platforms', methods=['GET'])
@login_required
def get_platforms():
    return jsonify({'success': True, 'data': load_platforms()})

@user_bp.route('/api/convert-url', methods=['POST'])
@login_required
def convert_url():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'message': 'Missing url'}), 400
        
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=15
        )
        final_url = r.url
        
        extracted_id = None
        
        # Check Facebook
        if 'facebook.com' in url or 'fb.watch' in url or 'fb.com' in url:
            qs_params = parse_qs(urlparse(final_url).query)
            post_id = qs_params.get("story_fbid", [None])[0]
            
            if post_id:
                extracted_id = post_id
            else:
                match = re.search(r"(?:fbid=|posts/|videos/|/p/|/share/p/)([a-zA-Z0-9_-]+)", final_url)
                if match:
                    post_id = match.group(1)
                    # Verify using Graph API
                    success, res_val = verify_fb_post_id(post_id)
                    if success:
                        extracted_id = res_val
                    else:
                        return jsonify({'success': False, 'message': res_val, 'final_url': final_url})
                else:
                    # Alternative regex matching just numbers at the end
                    alt_match = re.search(r"(\d+)/?$", final_url)
                    if alt_match:
                        post_id = alt_match.group(1)
                        success, res_val = verify_fb_post_id(post_id)
                        if success:
                            extracted_id = res_val
                        else:
                            return jsonify({'success': False, 'message': res_val, 'final_url': final_url})
        else:
            tt_match = re.search(r'/video/(\d+)', final_url)
            if tt_match:
                extracted_id = tt_match.group(1)
            else:
                ig_match = re.search(r'/(?:p|reel)/([a-zA-Z0-9_-]+)', final_url)
                if ig_match:
                    extracted_id = ig_match.group(1)
        
        if extracted_id:
            return jsonify({'success': True, 'id': extracted_id})
        else:
            return jsonify({'success': False, 'message': 'Không tìm thấy ID trong link.', 'final_url': final_url})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@user_bp.route('/api/jobs/<int:job_id>/verify', methods=['POST'])
@login_required
def verify_job(job_id):
    now = time.time()
    last_verify = session.get('last_verify', 0)
    if now - last_verify < 5:
        return jsonify({'success': False, 'message': f'Vui lòng đợi {int(5 - (now - last_verify))}s trước khi gửi yêu cầu tiếp.'}), 429
    session['last_verify'] = now
    session.modified = True
    
    system_config = load_system_config()
    daily_limit = system_config.get('daily_task_limit', 200)
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = Task.query.filter(Task.worker_id == current_user.id, Task.created_at >= today_start).count()
    if completed_today >= daily_limit:
        return jsonify({'success': False, 'message': f'Bạn đã đạt giới hạn {daily_limit} nhiệm vụ/ngày. Vui lòng quay lại vào ngày mai!'}), 403

    job = Job.query.get_or_404(job_id)
    
    selected_acc = SocialAccount.query.filter_by(
        user_id=current_user.id, 
        platform=job.platform, 
        is_selected=True, 
        is_deleted=False
    ).first()
    
    if not selected_acc:
        return jsonify({'success': False, 'message': f'Bạn chưa cấu hình hoặc chọn tài khoản {job.platform} đang làm việc ở góc trên phải màn hình.'}), 400
        
    existing_task = Task.query.filter_by(job_id=job.id, worker_id=current_user.id).first()
    if existing_task:
        return jsonify({'success': False, 'message': 'Bạn đã nhận thưởng cho nhiệm vụ này rồi.'}), 400
        
    # Check if the selected social account has already done ANY job with the same target_url and action_type
    duplicate_task = Task.query.join(Job).filter(
        Task.social_account_id == selected_acc.id,
        Job.target_url == job.target_url,
        Job.action_type == job.action_type
    ).first()
    if duplicate_task:
        return jsonify({'success': False, 'message': 'Tài khoản này đã thực hiện tương tác trên bài viết này ở một nhiệm vụ khác rồi.'}), 400
        
    if job.platform == 'FACEBOOK':
        post_id = job.target_url
        success, msg = check_fb_action_status(post_id, selected_acc.social_id, job.action_type)
        if not success:
            return jsonify({'success': False, 'message': msg}), 400
    else:
        # Tạm thời duyệt nhanh các nền tảng khác
        pass
        
    try:
        new_task = Task(
            job_id=job.id,
            worker_id=current_user.id,
            social_account_id=selected_acc.id,
            reward=job.price_per_action,
            status='VERIFIED'
        )
        db.session.add(new_task)
        
        current_user.balance += job.price_per_action
        
        tx = Transaction(
            user_id=current_user.id,
            amount=job.price_per_action,
            type='TASK_REWARD',
            status='SUCCESS',
            description=f'Nhận thưởng nhiệm vụ {job.action_type} - {job.platform}'
        )
        db.session.add(tx)
        
        job.current_count += 1
        if job.current_count >= job.quantity:
            job.status = 'COMPLETED'
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Nhận thưởng thành công!', 'reward': float(job.price_per_action)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Lỗi hệ thống khi nhận thưởng: ' + str(e)}), 500
