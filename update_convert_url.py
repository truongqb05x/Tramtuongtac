import codecs

with codecs.open('app/controllers/user_ctrl.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        # Check Facebook
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
                        extracted_id = result["id"]'''

replacement = '''        # Check Facebook
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
                            extracted_id = result["id"]'''

with codecs.open('app/controllers/user_ctrl.py', 'w', encoding='utf-8') as f:
    f.write(content.replace(target, replacement))

print("Updated")
