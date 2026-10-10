import requests
import re
import html
from urllib.parse import urlparse, parse_qs
from app.models.fb_token import FbToken
from app.extensions import db
def get_facebook_profile(url):
    uid = None
    name = None
    
    # Bước 1: Dùng linktoid.com API để lấy UID dạng số (vượt rào chặn IP)
    try:
        session = requests.Session()
        headers = {
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
        }
        page = session.get("https://linktoid.com/", headers=headers, timeout=20)
        
        csrf_token = session.cookies.get("XSRF-TOKEN")
        if csrf_token:
            from urllib.parse import unquote
            csrf_token = unquote(csrf_token)
        else:
            match = re.search(r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)', page.text, re.IGNORECASE)
            csrf_token = match.group(1) if match else None

        req_headers = {
            **headers,
            "Content-Type": "application/json",
            "Origin": "https://linktoid.com",
            "Referer": "https://linktoid.com/",
        }
        if csrf_token:
            req_headers["X-CSRF-TOKEN"] = csrf_token

        resp = session.post(
            "https://linktoid.com/api/convert-id",
            headers=req_headers,
            json={"link": url.strip()},
            timeout=30
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("success") and result.get("id"):
                uid = str(result["id"])
    except Exception:
        pass
        
    # Bước 2: Nếu lấy được uid, kết hợp dùng FbToken gọi Graph API để lấy name (vì linktoid không có name)
    if uid:
        active_tokens = FbToken.query.filter_by(is_active=True).all()
        if active_tokens:
            for t in active_tokens:
                graph_url = f"https://graph.facebook.com/{uid}"
                params = {"fields": "id,name", "access_token": t.token}
                try:
                    res = requests.get(graph_url, params=params, timeout=10).json()
                    if "name" in res:
                        name = res["name"]
                        break
                    else:
                        error_data = res.get('error', {})
                        error_msg = error_data.get('message', '').lower()
                        error_code = error_data.get('code')
                        if 'access token' in error_msg or 'session has been invalidated' in error_msg or error_code in [190, 2500, 104, 12]:
                            t.is_active = False
                            db.session.commit()
                except Exception:
                    continue

    if not uid:
        # Bước 3: Fallback lấy phần cuối URL làm uid nếu linktoid bị lỗi
        parsed_url = urlparse(url)
        social_id = url.rstrip('/').split('/')[-1]
        if 'profile.php' in parsed_url.path:
            qs = parse_qs(parsed_url.query)
            if 'id' in qs:
                social_id = qs['id'][0]
        uid = social_id

    return {
        "uid": uid,
        "name": name,
        "url": url,
        "status": 200 if uid else 500
    }

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
                
                if 'access token' in error_msg or 'session has been invalidated' in error_msg or error_code in [190, 2500, 104, 12]:
                    t.is_active = False
                    db.session.commit()
                    continue
                else:
                    return False, "Lỗi Graph API: " + error_data.get('message', 'Không thể xác định bài viết')
        except requests.RequestException:
            continue
            
    return False, "Tất cả Token đều bị lỗi."

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
    
    if action_type not in ['LIKE', 'LOVE', 'WOW', 'HAHA', 'SAD']:
        return True, "Mock: Tạm duyệt (chỉ LIKE/REACTION mới check API)."
        
    for t in active_tokens:
        url = f"https://graph.facebook.com/v23.0/{post_id}/reactions"
        params = {"access_token": t.token, "fields": "id,type", "limit": 100}
        
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
                    if user.get("type") == action_type and str(user.get("id")) == str(user_uid):
                        return True, "Đã thực hiện"
                
                url = data.get("paging", {}).get("next")
                params = None
            
            if not token_failed:
                return False, f"Chưa tìm thấy lượt {action_type} của bạn trên bài viết này (Hoặc cấu hình sai UID)."
                
        except requests.RequestException:
            continue
            
    return False, "Hệ thống Token đang gặp lỗi toàn bộ."
