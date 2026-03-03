import os
import ast
import re

def analyze_python(path):
    """Извлекает функции и классы из Python-файла"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        return {"functions": functions, "classes": classes}
    except Exception:
        return {"functions": [], "classes": []}

def analyze_js(path):
    """Ищет JS-функции в HTML файле через регулярки"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        functions = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', content)
        return {"functions": functions}
    except Exception:
        return {"functions": []}

files = {
    'backend/main.py': 'Python (API)',
    'backend/models.py': 'Python (DB Models)',
    'backend/database.py': 'Python (DB Config)',
    'bot.py': 'Python (Telegram Bot)',
    'frontend/index.html': 'HTML/JS (UI)',
    '.env': 'Config (Environment)'
}

print('--- 🛠 SAFESPACE: ПОЛНЫЙ АНАЛИЗ ПРОЕКТА ---')

for path, desc in files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"\n✅ {path} ({size} байт) — {desc}")
        
        # Анализ содержимого
        if path.endswith('.py'):
            data = analyze_python(path)
            if data['classes']: print(f"   ∟ 🏛 Классы: {', '.join(data['classes'])}")
            if data['functions']: print(f"   ∟ ⚙️ Функции: {', '.join(data['functions'])}")
            
        elif path.endswith('.html'):
            data = analyze_js(path)
            if data['functions']: print(f"   ∟ ⚡ JS-Логика: {', '.join(data['functions'])}")
            
        elif path == '.env':
            with open(path, 'r') as f:
                keys = [line.split('=')[0] for line in f if '=' in line]
                print(f"   ∟ 🔑 Настройки: {', '.join(keys)}")
    else:
        print(f"\n❌ {path} — ФАЙЛ ОТСУТСТВУЕТ")

print('\n' + '='*40)
print('📂 СТРУКТУРА ПАПОК:')
for root, dirs, filenames in os.walk('.'):
    if '.git' in root or '__pycache__' in root: continue
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 4 * (level)
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 4 * (level + 1)
    for f in filenames:
        print(f'{subindent}{f}')