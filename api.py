import requests

GRAPH_VERSION = "v23.0"
ACCESS_TOKEN = "EAAAAUaZA8jlABSYVbO8IZAUdw72Gyt2XbZCW5fM9sBVAhDb8ciKULlj3sRDNXs1aPpWnztXUhbHg1faE3c4vSGHLtdZATl2jRUYxvaVFduCq2UXOZACOOTW7xXPnJfbM6Ch7pEZCqFdF7FwkISXe05gw3ZBBaQfNReSaqcFJSuMLbrZCMYoYz0hzbaInFG4HZBSZBSAYD4q1QE3wZDZD"


def get_like_uids(post_id):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{post_id}/reactions"

    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "id,type",
        "limit": 100
    }

    like_uids = []

    while url:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        data = response.json()

        if response.status_code != 200:
            print("Graph API Error:")
            print(data)
            return []

        for user in data.get("data", []):
            if user.get("type") == "LIKE":
                uid = user.get("id")

                if uid:
                    like_uids.append(uid)

        url = data.get("paging", {}).get("next")
        params = None

    return like_uids


post_id = input("Nhập Post ID: ").strip()

uids = get_like_uids(post_id)

print("\nDanh sách UID LIKE:")

for uid in uids:
    print(uid)

print(f"\nTổng LIKE: {len(uids)}")