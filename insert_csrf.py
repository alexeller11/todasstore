import os

template_dir = r"C:\Users\alex_\.gemini\antigravity\scratch\todasstore\app\templates"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = ""
    i = 0
    changed = False
    while i < len(content):
        if content[i:i+5].lower() == "<form":
            start_idx = i
            end_idx = content.find(">", i)
            if end_idx != -1:
                tag = content[start_idx:end_idx+1]
                if 'METHOD="POST"' in tag.upper() or "METHOD='POST'" in tag.upper():
                    if 'csrf_token' not in content[i:i+300]:
                        new_content += tag + '\n    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>'
                        i = end_idx + 1
                        changed = True
                        continue
        new_content += content[i]
        i += 1

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes for {filepath}")

for root, _, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            process_file(os.path.join(root, f))
