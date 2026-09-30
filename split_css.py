import os
import re

css_path = r'C:\Users\lab\Downloads\Tramtuongtac\static\css\layout\layout_admin\layout_admin.css'
out_dir = r'C:\Users\lab\Downloads\Tramtuongtac\static\css\layout\layout_admin'

with open(css_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by the comment blocks /* ---------- ... ---------- */
sections = re.split(r'/\*\s*-+\s*(.*?)\s*-+\s*\*/', content)

# sections[0] is the base/variables before the first comment
blocks = {'base': sections[0].strip()}

for i in range(1, len(sections), 2):
    title = sections[i].lower()
    code = sections[i+1].strip()
    
    if 'sidebar' in title:
        blocks['sidebar'] = blocks.get('sidebar', '') + '\n\n' + code
    elif 'topbar' in title:
        blocks['topbar'] = blocks.get('topbar', '') + '\n\n' + code
    elif 'content' in title or 'panel' in title:
        blocks['layout'] = blocks.get('layout', '') + '\n\n' + code
    elif 'modal' in title or 'toast' in title or 'config' in title:
        blocks['modals'] = blocks.get('modals', '') + '\n\n' + code
    else:
        blocks['components'] = blocks.get('components', '') + '\n\n' + code

# Write files
imports = []
for name, code in blocks.items():
    if code:
        file_name = f"{name}.css"
        with open(os.path.join(out_dir, file_name), 'w', encoding='utf-8') as f:
            f.write(code + '\n')
        imports.append(f'@import url("{file_name}");')

with open(os.path.join(out_dir, 'admin.css'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(imports) + '\n')

print("Success")
