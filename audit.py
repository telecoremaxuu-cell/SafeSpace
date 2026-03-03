import os
import re
import sqlite3
import subprocess
from datetime import datetime

def get_db_stats():
    db_path = 'safespace.db'
    if not os.path.exists(db_path): return "❌ БАЗА ОТСУТСТВУЕТ"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        cursor.execute("SELECT count(*) FROM users")
        u_count = cursor.fetchone()[0]
        conn.close()
        return f"✅ OK (Юзеров: {u_count}, Таблицы: {', '.join(tables)})"
    except Exception as e: return f"⚠️ Ошибка: {e}"

def deep_scan_file(path):
    """Извлекает ключевые элементы кода для понимания структуры"""
    info = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем эндпоинты FastAPI
            if 'main.py' in path:
                routes = re.findall(r'@app\.(get|post|put|delete)\("([^"]+)"\)', content)
                for method, route in routes: info.append(f"📡 API: {method.upper()} {route}")
            # Ищем функции бота
            elif 'bot.py' in path:
                handlers = re.findall(r'@dp\.(message|callback_query)\(([^)]+)\)', content)
                for h_type, cond in handlers: info.append(f"🤖 Bot: {h_type} ({cond.strip()})")
            # Ищем интерактив в HTML
            elif 'index.html' in path:
                ids = re.findall(r'id="([^"]+)"', content)
                for i in ids[:5]: info.append(f"🎨 UI Element: #{i}") # берем первые 5
    except: pass
    return info

def analyze_project():
    print(f'\n{"="*60}')
    print(f'🚀 SAFESPACE PRO-AUDIT | {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
    print(f'{"="*60}')
    
    # 1. СТАТУС СИСТЕМЫ
    print("\n📊 СИСТЕМНЫЙ СЛОЙ:")
    print(f"   ∟ База данных: {get_db_stats()}")
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_keys = [line.split('=')[0] for line in f if '=' in line]
            print(f"   ∟ Конфиг (.env): ✅ Загружено ({', '.join(env_keys)})")
    else:
        print("   ∟ Конфиг (.env): ❌ ФАЙЛ НЕ НАЙДЕН")

    # 2. ГЛУБОКИЙ АНАЛИЗ КОДА
    print("\n🧠 АНАЛИЗ ЛОГИКИ (DEEP SCAN):")
    important_files = ['backend/main.py', 'bot.py', 'index.html']
    for file in important_files:
        if os.path.exists(file):
            print(f"   📂 {file}:")
            features = deep_scan_file(file)
            for feat in features:
                print(f"      └── {feat}")
        else:
            print(f"   📂 {file}: ❌ Файл не найден")

    # 3. ПРОВЕРКА БЕЗОПАСНОСТИ
    print("\n🛡 БЕЗОПАСНОСТЬ:")
    security_flag = True
    for file in ['bot.py', 'backend/main.py']:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                if re.search(r'[0-9]{8,10}:[a-zA-Z0-9_-]{35}', f.read()):
                    print(f"   ⚠️ ВНИМАНИЕ: Токен бота найден прямо в {file}! Перенеси в .env")
                    security_flag = False
    if security_flag: print("   ✅ Секретные ключи не обнаружены в коде.")

    # 4. ФАЙЛОВАЯ СТРУКТУРА
    print("\n📁 ФИЗИЧЕСКАЯ СТРУКТУРА:")
    skip = {'.git', '__pycache__', 'venv'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in skip]
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 3 * level
        print(f'{indent}📁 {os.path.basename(root) or "."}/')
        for f in files:
            f_path = os.path.join(root, f)
            size = os.path.getsize(f_path)
            s_str = f"{size}b" if size < 1024 else f"{size/1024:.1f}kb"
            print(f'{indent}   └── 📄 {f} ({s_str})')

    print(f'\n{"="*60}')

if __name__ == "__main__":
    analyze_project()