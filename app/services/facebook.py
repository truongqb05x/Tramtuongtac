import requests
import re
import html
from urllib.parse import urlparse, parse_qs
from app.models.fb_token import FbToken
from app.extensions import db
def get_facebook_profile(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=30
        )

        source = response.text

        # =========================
        # LẤY UID
        # =========================

        uid_patterns = [
            r'fb://profile/(\d+)',
            r'"profile_id"\s*:\s*"(\d+)"',
            r'"userID"\s*:\s*"(\d+)"',
            r'"user_id"\s*:\s*"(\d+)"',
            r'"entity_id"\s*:\s*"(\d+)"',
        ]

        uid = None

        for pattern in uid_patterns:
            match = re.search(pattern, source, re.I)
            if match:
                uid = match.group(1)
                break

        # =========================
        # LẤY NAME
        # =========================

        name = None
        name_patterns = [
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, source, re.I)
            if match:
                name = html.unescape(match.group(1)).strip()
                break

        return {
            "uid": uid,
            "name": name,
            "url": response.url,
            "status": response.status_code
        }

    except requests.RequestException as e:
        return {
            "uid": None,
            "name": None,
            "url": url,
            "status": None,
            "error": str(e)
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
