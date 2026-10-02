import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../instance/system.json')

DEFAULT_CONFIG = {
    "maintenance_mode": False,
    "safe_mode": False,
    "platform_fee": 10,
    "min_quantity": 5,
    "daily_task_limit": 200
}

def load_system_config():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        save_system_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Fill missing keys with defaults
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_system_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_system_field(key, value):
    """Update a single key in system config without overwriting the rest."""
    cfg = load_system_config()
    cfg[key] = value
    save_system_config(cfg)
    return cfg
