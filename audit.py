import os
import re
import sqlite3
import subprocess
import socket
from datetime import datetime

# Цвета для терминала
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    WHITE = '\033[97m'
    END = '\033[0m'

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('localhost', port)) == 0

def fix_bom(path):
    """Принудительное удаление BOM и пересохранение"""
    try:
        with open(path, 'rb') as f:
            content = f.read()
        if content.startswith(b'\xef\xbb\xbf'):
            decoded = content.decode('utf-8-sig')
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(decoded)
            return True
    except: pass
    return False

def get_db_stats():
    db_path = 'safespace.db'
    if not os.path.exists(db_path): return f"{Colors.RED}❌ ОТСУТСТВУЕТ{Colors.END}"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        # Проверка структуры (чтобы AM не забыл поля)
        db_info = ""
        if 'users' in tables:
            cursor.execute("PRAGMA table_info(users)")
            cols = [c[1] for c in cursor.fetchall()]
            cursor.execute("SELECT count(*) FROM users")
            u_count = cursor.fetchone()[0]
            db_info = f"(Юзеров: {u_count}, Колонки: {', '.join(cols)})"
        
        conn.close()
        return f"{Colors.GREEN}✅ OK{Colors.END} {db_info}"
    except Exception as e: return f"{Colors.YELLOW}⚠️ Ошибка БД: {e}{Colors.END}"

def deep_scan_logic():
    issues = []
    fixed_files = []
    logic = {"api": [], "calls": []}
    
    # 1. ТОТАЛЬНАЯ ПРОВЕРКА И АВТО-ЛЕЧЕНИЕ BOM
    for root, _, files in os.walk('.'):
        if any(part in root for part in ['.git', '__pycache__', 'venv', 'env', 'node_modules']):
            continue
        for file in files:
            if file.endswith(('.py', '.html', '.js', '.css', '.env')):
                path = os.path.join(root, file)
                if fix_bom(path):
                    fixed_files.append(path)

    # 2. Сканируем Backend (main.py)
    if os.path.exists('backend/main.py'):
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            logic["api"] = re.findall(r'@app\.(?:get|post|put|delete)\("([^"]+)"\)', content)
            has_auto_reg = "db.add" in content and ("if not user" in content or "upsert" in content)
            if not has_auto_reg:
                issues.append(f"{Colors.RED}❗ ЛОГИЧЕСКАЯ ОШИБКА: Нет авто-регистрации!{Colors.END}")
            if "CORSMiddleware" not in content:
                issues.append(f"{Colors.YELLOW}⚠️ БЕЗОПАСНОСТЬ: CORS не настроен!{Colors.END}")

    # 3. Сканируем Frontend (index.html)
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            if "127.0.0.1" in content or "localhost" in content:
                issues.append(f"{Colors.RED}❗ СЕТЬ: В коде найден localhost!{Colors.END}")
            logic["calls"] = re.findall(r'fetch\([\'\"`]?(?:\${API_URL})?([^?\'\"`\s]+)', content)
            if "telegram-web-app.js" not in content:
                issues.append(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Telegram SDK не найден!{Colors.END}")

    # 4. Проверка порта
    if not check_port(8000):
        issues.append(f"{Colors.YELLOW}⚠️ СЕРВЕР: Порт 8000 не отвечает. Запусти uvicorn!{Colors.END}")

    # Сверка эндпоинтов
    for call in logic["calls"]:
        clean_call = re.sub(r'\${[^}]+}', '{id}', call).split('?')[0]
        if not any(re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', api), clean_call) or clean_call in api for api in logic["api"]):
            if clean_call != "/" and not clean_call.startswith('http'):
                issues.append(f"{Colors.YELLOW}⚠️ СИНХРО: Фронт вызывает {clean_call}, бэкенд — нет!{Colors.END}")

    return logic, issues, fixed_files

def analyze_project():
    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')
    print(f'🚀 {Colors.WHITE}SAFESPACE COMMANDER AUDIT v6.0{Colors.END} | {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
    print(f'{Colors.PURPLE}{"#"*60}{Colors.END}')
    
    # 1. БД
    print(f"\n📡 {Colors.CYAN}СИСТЕМНЫЙ СЛОЙ:{Colors.END}")
    print(f"   ∟ База данных: {get_db_stats()}")
    
    # 2. ЛОГИКА И ЛЕЧЕНИЕ
    print(f"\n🧠 {Colors.CYAN}АНАЛИЗ И АВТО-ИСПРАВЛЕНИЕ:{Colors.END}")
    logic, issues, fixed = deep_scan_logic()
    
    if fixed:
        for f in fixed:
            print(f"   {Colors.GREEN}🛠 ИСПРАВЛЕНО: Убран BOM из {f}{Colors.END}")
    
    if not issues:
        print(f"   {Colors.GREEN}✅ Все системы синхронизированы.{Colors.END}")
    else:
        for issue in issues:
            print(f"   {issue}")

    # 3. ФИЗИЧЕСКАЯ СТРУКТУРА (Твоя полная версия)
    print(f"\n📁 {Colors.CYAN}СТРУКТУРА И ВЕС:{Colors.END}")
    skip = {'.git', '__pycache__', 'venv', 'env', 'node_modules'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in skip]
        level = root.replace('.', '').count(os.sep)
        indent = '   ' * level
        print(f'{indent}📁 {os.path.basename(root) or "."}/')
        for f in files:
            f_path = os.path.join(root, f)
            try:
                size = os.path.getsize(f_path)
                s_str = f"{size}b" if size < 1024 else f"{size/1024:.1f}kb"
                print(f'{indent}   └── 📄 {f} ({s_str})')
            except: pass

    # 4. ГИТ (Твоя полная версия)
    print(f"\n📦 {Colors.CYAN}GIT СТАТУС:{Colors.END}")
    try:
        git_res = subprocess.check_output("git status -s", shell=True).decode()
        if git_res:
            print(f"   {Colors.YELLOW}📂 Есть незакоммиченные файлы.{Colors.END}")
        else:
            print(f"   {Colors.GREEN}✅ Чисто.{Colors.END}")
    except:
        print(f"   {Colors.RED}❌ Git Error{Colors.END}")

    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')

if __name__ == "__main__":
    analyze_project()