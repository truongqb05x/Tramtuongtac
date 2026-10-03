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
        
        if quantity < 5:
            return jsonify({'success': False, 'message': 'Số lượng tối thiểu phải từ 5 trở lên'}), 400
            
        if current_user.balance < total_cost:
            return jsonify({'success': False, 'message': 'Không đủ Credits'}), 400
            
        from app.services.system_cfg import load_system_config
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
        
    from app.services.system_cfg import load_system_config
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
    from app.models.user import SocialAccount
    has_accounts = SocialAccount.query.filter_by(user_id=current_user.id, is_deleted=False).first() is not None
    # Fetch running jobs that are not deleted
    db_jobs = Job.query.filter_by(status='RUNNING', is_deleted=False).all()
    jobs_data = [job.to_dict() for job in db_jobs]
    from app.services.system_cfg import load_system_config
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
            
        if not check_password_hash(current_user.password_hash, current_pass):
            return jsonify({'success': False, 'message': 'Mật khẩu hiện tại không đúng.'}), 400
            
        if len(new_pass) < 6:
            return jsonify({'success': False, 'message': 'Mật khẩu mới phải có ít nhất 6 ký tự.'}), 400
            
        current_user.password_hash = generate_password_hash(new_pass).decode('utf-8')
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
        
        account_name = None
        if platform == 'FACEBOOK':
            from app.services.facebook import get_facebook_profile
            fb_info = get_facebook_profile(url)
            if fb_info.get('uid'):
                social_id = fb_info['uid']
                url = fb_info.get('url', url)
                account_name = fb_info.get('name')
                
        # Check if it already exists
        existing_acc = SocialAccount.query.filter_by(platform=platform, social_id=social_id).first()
        if existing_acc:
            return jsonify({'success': False, 'message': 'Tài khoản này đã tồn tại trong hệ thống'}), 400
        
        from app.services.system_cfg import load_system_config
        config = load_system_config()
        is_safe_mode = config.get('safe_mode', False)
        initial_status = 'PENDING' if is_safe_mode else 'ACTIVE'

        acc = SocialAccount(
            user_id=current_user.id,
            platform=platform,
            profile_url=url,
            social_id=social_id,
            account_name=account_name,
            status=initial_status
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
                'active': False,
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
            'name': a.account_name if a.account_name else a.social_id,
            'verified': a.status == 'ACTIVE',
            'status': a.status.lower(),
            'active': a.is_selected,
            'addedAt': a.created_at.strftime('%Y-%m-%d')
        })
        
    from app.services.platform_cfg import load_platforms
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

from app.services.platform_cfg import load_platforms

@user_bp.route('/api/platforms', methods=['GET'])
@login_required
def get_platforms():
    return jsonify({'success': True, 'data': load_platforms()})


import requests
import re
from urllib.parse import urlparse, parse_qs

import random
from app.models.fb_token import FbToken

def verify_fb_post_id(post_id):
    active_tokens = FbToken.query.filter_by(is_active=True).all()
    if not active_tokens:
        return False, "Chưa cấu hình Token hoặc Token lỗi hết. Vui lòng báo Admin để nạp Token."
        
    for t in active_tokens:
        graph_url = f"https://graph.facebook.com/{post_id}"
        params = {"fields": "id", "access_token": t.token}
        try:
            res = requests.get(graph_url, params=params, timeout=15).json()
            if "id" in res:
                return True, res["id"]
            else:
                error_data = res.get('error', {})
                error_msg = error_data.get('message', '').lower()
                error_code = error_data.get('code')
                
                # Check if token is invalid or expired
                if 'access token' in error_msg or 'session has been invalidated' in error_msg or error_code in [190, 2500, 104]:
                    t.is_active = False
                    db.session.commit()
                    continue
                else:
                    return False, "Lỗi Graph API: " + error_data.get('message', 'Không thể xác định bài viết')
        except requests.RequestException:
            continue
            
    return False, "Tất cả Token đều bị lỗi."

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

from app.models.job import Job
from app.models.task import Task
from app.models.transaction import Transaction

def extract_fbid(final_url):
    qs_params = parse_qs(urlparse(final_url).query)
    post_id = qs_params.get('story_fbid', [None])[0]
    if post_id: return post_id
    match = re.search(r"(?:fbid=|posts/|videos/|/p/|/share/p/)([a-zA-Z0-9_-]+)", final_url)
    if match: return match.group(1)
    alt_match = re.search(r"(\d+)/?$", final_url)
    if alt_match: return alt_match.group(1)
    return None

def check_fb_action_status(post_id, user_uid, action_type):
    active_tokens = FbToken.query.filter_by(is_active=True).all()
    if not active_tokens:
        return False, "Chưa cấu hình Token hoặc Token lỗi hết. Vui lòng báo Admin để nạp Token."
    
    if action_type != 'LIKE':
        return True, "Mock: Tạm duyệt (chỉ LIKE mới check API)."
        
    for t in active_tokens:
        url = f"https://graph.facebook.com/v23.0/{post_id}/reactions"
        params = {
            "access_token": t.token,
            "fields": "id,type",
            "limit": 100
        }
        
        try:
            token_failed = False
            while url:
                response = requests.get(url, params=params, timeout=15)
                data = response.json()
                
                if response.status_code != 200:
                    error_data = data.get('error', {})
                    error_msg = error_data.get('message', '').lower()
                    error_code = error_data.get('code')
                    
                    if 'access token' in error_msg or 'session has been invalidated' in error_msg or error_code in [190, 2500, 104, 12]:
                        t.is_active = False
                        db.session.commit()
                        token_failed = True
                        break 
                    else:
                        return False, f"Lỗi Graph API: {error_data.get('message')}"
                
                for user in data.get("data", []):
                    if user.get("type") == "LIKE" and str(user.get("id")) == str(user_uid):
                        return True, "Đã thực hiện"
                
                url = data.get("paging", {}).get("next")
                params = None
            
            if not token_failed:
                return False, "Chưa tìm thấy lượt LIKE của bạn trên bài viết này (Hoặc cấu hình sai UID)."
                
        except requests.RequestException:
            continue
            
    return False, "Hệ thống Token đang gặp lỗi toàn bộ."

@user_bp.route('/api/jobs/<int:job_id>/verify', methods=['POST'])
@login_required
def verify_job(job_id):
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
        
    if job.platform == 'FACEBOOK':
        post_id = extract_fbid(job.target_url)
        if not post_id:
            return jsonify({'success': False, 'message': 'Không nhận diện được Facebook ID từ link nhiệm vụ.'}), 400
            
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
