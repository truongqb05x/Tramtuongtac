import requests
import re
import html

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
