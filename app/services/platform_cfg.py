import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../instance/platforms.json')

DEFAULT_CONFIG = [
    {
        "id": "facebook",
        "name": "Facebook",
        "active": True,
        "activities": [
            {"id": "fb_like", "name": "👍 Tăng Like Bài Viết", "price": 20, "active": True},
            {"id": "fb_follow", "name": "👥 Tăng Follow / Sub", "price": 30, "active": True},
            {"id": "fb_comment", "name": "💬 Tăng Bình Luận", "price": 50, "active": True}
        ]
    },
    {
        "id": "tiktok",
        "name": "TikTok",
        "active": False,
        "activities": [
            {"id": "tt_heart", "name": "❤️ Tăng Tim Video", "price": 25, "active": True},
            {"id": "tt_follow", "name": "👥 Tăng Follow Kênh", "price": 35, "active": True}
        ]
    }
]

def load_platforms():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        save_platforms(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_platforms(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
