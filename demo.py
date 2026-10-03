import requests
from urllib.parse import urlparse, parse_qs

url = "https://www.facebook.com/share/p/1EczTupFoL/?mibextid=wwXIfr"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(
    url,
    headers=headers,
    allow_redirects=True,
    timeout=15
)

final_url = r.url

# Lấy query parameters
params = parse_qs(urlparse(final_url).query)

post_id = params.get("story_fbid", [None])[0]

print("\nPost ID:")
print(post_id)