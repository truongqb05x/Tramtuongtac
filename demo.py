import requests
import re

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

print("Final URL:")
print(r.url)