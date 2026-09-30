import re

def revert_jinja():
    with open('templates/admin/layout_admin.html', 'r', encoding='utf-8') as f:
        layout = f.read()

    with open('templates/admin/Admin.html', 'r', encoding='utf-8') as f:
        admin = f.read()

    # Extract blocks from Admin.html
    title_match = re.search(r'\{%\s*block title\s*%\}(.*?)\{%\s*endblock\s*%\}', admin, re.DOTALL)
    title_content = title_match.group(1).strip() if title_match else 'Dashboard - Admin Console'

    content_match = re.search(r'\{%\s*block content\s*%\}(.*?)\{%\s*endblock\s*%\}', admin, re.DOTALL)
    content_content = content_match.group(1).strip() if content_match else ''

    js_match = re.search(r'\{%\s*block extra_js\s*%\}(.*?)\{%\s*endblock\s*%\}', admin, re.DOTALL)
    js_content = js_match.group(1).strip() if js_match else ''

    # Reconstruct Admin.html
    merged = layout
    merged = re.sub(r'\{%\s*block title\s*%\}.*?\{%\s*endblock\s*%\}', title_content, merged, flags=re.DOTALL)
    merged = re.sub(r'\{%\s*block extra_css\s*%\}.*?\{%\s*endblock\s*%\}', '', merged, flags=re.DOTALL)
    merged = re.sub(r'\{%\s*block content\s*%\}.*?\{%\s*endblock\s*%\}', content_content, merged, flags=re.DOTALL)
    merged = re.sub(r'\{%\s*block extra_js\s*%\}.*?\{%\s*endblock\s*%\}', js_content, merged, flags=re.DOTALL)

    with open('templates/admin/Admin.html', 'w', encoding='utf-8') as f:
        f.write(merged)

    # Clean up layout_admin.html to be a boilerplate template
    clean_layout = layout
    clean_layout = re.sub(r'\{%\s*block title\s*%\}(.*?)\{%\s*endblock\s*%\}', r'\1', clean_layout, flags=re.DOTALL)
    clean_layout = re.sub(r'\{%\s*block extra_css\s*%\}.*?\{%\s*endblock\s*%\}', '', clean_layout, flags=re.DOTALL)
    clean_layout = re.sub(r'\{%\s*block content\s*%\}.*?\{%\s*endblock\s*%\}', '<!-- Nội dung trang con sẽ nằm ở đây -->', clean_layout, flags=re.DOTALL)
    clean_layout = re.sub(r'\{%\s*block extra_js\s*%\}.*?\{%\s*endblock\s*%\}', '<!-- Script riêng của trang con sẽ nằm ở đây -->', clean_layout, flags=re.DOTALL)

    with open('templates/admin/layout_admin.html', 'w', encoding='utf-8') as f:
        f.write(clean_layout)

    print("Success")

if __name__ == '__main__':
    revert_jinja()
