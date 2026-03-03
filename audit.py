import os
import re
import sqlite3
import subprocess
import socket
from datetime import datetime

# Цвета для терминала (чтобы сразу видеть косяки)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    WHITE = '\033[97m'
    END = '\033[0m'

def check_port(port):
    """Проверка, запущен ли сервер на самом деле"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_db_stats():
    db_path = 'safespace.db'
    if not os.path.exists(db_path): return f"{Colors.RED}❌ ОТСУТСТВУЕТ{Colors.END}"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        cursor.execute("SELECT count(*) FROM users")
        u_count = cursor.fetchone()[0]
        conn.close()
        return f"{Colors.GREEN}✅ OK{Colors.END} (Юзеров: {u_count}, Таблицы: {', '.join(tables)})"
    except Exception as e: return f"{Colors.YELLOW}⚠️ Ошибка: {e}{Colors.END}"

def deep_scan_logic():
    issues = []
    logic = {"api": [], "calls": []}
    
    # 1. ТОТАЛЬНАЯ ПРОВЕРКА НА BOM (U+FEFF) ПО ВСЕМУ ПРОЕКТУ
    for root, _, files in os.walk('.'):
        if any(part in root for part in ['.git', '__pycache__', 'venv', 'env', 'node_modules']):
            continue
        for file in files:
            if file.endswith(('.py', '.html', '.js', '.css', '.env')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        if f.read(3) == b'\xef\xbb\xbf':
                            issues.append(f"{Colors.RED}❗ КРИТИЧЕСКАЯ ОШИБКА: Файл {path} сохранен с BOM!{Colors.END}")
                except: pass

    # 2. Сканируем Backend (main.py)
    if os.path.exists('backend/main.py'):
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            logic["api"] = re.findall(r'@app\.(?:get|post|put|delete)\("([^"]+)"\)', content)
            
            # Проверка ИНТЕЛЛЕКТА (Авто-регистрация)
            has_auto_reg = "db.add" in content and ("if not user" in content or "upsert" in content)
            if not has_auto_reg:
                issues.append(f"{Colors.RED}❗ ЛОГИЧЕСКАЯ ОШИБКА: Приложение не умеет само добавлять юзеров!{Colors.END}")
            
            # Проверка CORS (Критично для работы с телефона)
            if "CORSMiddleware" not in content:
                issues.append(f"{Colors.YELLOW}⚠️ БЕЗОПАСНОСТЬ: CORS не настроен. Телефон может не подключиться!{Colors.END}")

    # 3. Сканируем Frontend (index.html)
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            # ПРОВЕРКА НА LOCALHOST
            if "127.0.0.1" in content or "localhost" in content:
                issues.append(f"{Colors.RED}❗ КРИТИЧЕСКАЯ ОШИБКА: В index.html найден 127.0.0.1. Бот не заработает на телефоне!{Colors.END}")
            
            # Ищем вызовы fetch
            logic["calls"] = re.findall(r'fetch\([\'\"`]?(?:\${API_URL})?([^?\'\"`\s]+)', content)
            
            # Проверка Telegram SDK
            if "telegram-web-app.js" not in content:
                issues.append(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Telegram SDK не найден в index.html!{Colors.END}")

    # 4. Проверка активности порта 8000
    if not check_port(8000):
        issues.append(f"{Colors.YELLOW}⚠️ СЕТЬ: Сервер (порт 8000) не отвечает. Uvicorn запущен?{Colors.END}")

    # Сверяем эндпоинты
    for call in logic["calls"]:
        clean_call = re.sub(r'\${[^}]+}', '{id}', call).split('?')[0]
        match_found = False
        for api in logic["api"]:
            pattern = re.sub(r'\{[^}]+\}', '[^/]+', api)
            if re.fullmatch(pattern, clean_call) or clean_call in api:
                match_found = True
                break
        if not match_found and clean_call != "/" and not clean_call.startswith('http'):
            issues.append(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Frontend вызывает {clean_call}, но в Backend такого эндпоинта нет!{Colors.END}")

    return logic, issues

def analyze_project():
    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')
    print(f'🚀 {Colors.WHITE}SAFESPACE ULTIMATE COMMANDER AUDIT v5.0{Colors.END} | {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
    print(f'{Colors.PURPLE}{"#"*60}{Colors.END}')
    
    # 1. СТАТУС СИСТЕМЫ
    print(f"\n📡 {Colors.CYAN}СИСТЕМНЫЙ СЛОЙ:{Colors.END}")
    print(f"   ∟ База данных: {get_db_stats()}")
    
    # 2. ПРОВЕРКА СВЯЗЕЙ И ИНТЕЛЛЕКТА
    print(f"\n🧠 {Colors.CYAN}АНАЛИЗ ЛОГИКИ И СЕТИ:{Colors.END}")
    logic, issues = deep_scan_logic()
    
    if not issues and logic.get("api"):
        print(f"   {Colors.GREEN}✅ Все системы синхронизированы. Ошибок не обнаружено.{Colors.END}")
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
            print(f"   {Colors.YELLOW}📂 Есть незакоммиченные файлы. Пора сделать push!{Colors.END}")
        else:
            print(f"   {Colors.GREEN}✅ Чисто. Все изменения в репозитории.{Colors.END}")
    except:
        print(f"   {Colors.RED}❌ Git не инициализирован или не найден.{Colors.END}")

    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')

if __name__ == "__main__":
    analyze_project()