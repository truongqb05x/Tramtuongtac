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

ACCESS_TOKEN = "EAAAAUaZA8jlABQZBcwm1lx2UxPnfxha9iWZBGodkjwi4EZCqa9UYsDrKICqR38IM7qxBEd3LD4kJLgiNqCyBhPAOR15y1sxotMURQdHiqWdBG6fg4AZA0yNjuW0DaSGyEuVPCAdIdtZAePI2qvWXXMYZAoMPlXmxr1e3AJd23JjrFBYhNGKYkJUcP5gHXFQdtf5mU1ZBygZDZD"

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
            match = re.search(r"(?:fbid=|story_fbid=|posts/|videos/|/p/|/share/p/)([a-zA-Z0-9_-]+)", final_url)
            if match:
                post_id = match.group(1)
                # Verify using Graph API
                graph_url = f"https://graph.facebook.com/{post_id}"
                params = {
                    "fields": "id",
                    "access_token": ACCESS_TOKEN
                }
                result = requests.get(graph_url, params=params, timeout=15).json()
                if "id" in result:
                    extracted_id = result["id"]
                else:
                    return jsonify({'success': False, 'message': 'Lỗi Graph API: ' + str(result.get('error', {}).get('message', 'Không thể xác thực bài viết FB')), 'final_url': final_url})
            else:
                # Alternative regex matching just numbers at the end
                alt_match = re.search(r"(\d+)/?$", final_url)
                if alt_match:
                    post_id = alt_match.group(1)
                    graph_url = f"https://graph.facebook.com/{post_id}"
                    params = {
                        "fields": "id",
                        "access_token": ACCESS_TOKEN
                    }
                    result = requests.get(graph_url, params=params, timeout=15).json()
                    if "id" in result:
                        extracted_id = result["id"]
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
