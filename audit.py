import os
import re
import sqlite3
import subprocess
from datetime import datetime

# Цвета для терминала (чтобы сразу видеть косяки)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    END = '\033[0m'

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
    
    # Сканируем Backend
    if os.path.exists('backend/main.py'):
        with open('backend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            logic["api"] = re.findall(r'@app\.(?:get|post)\("([^"]+)"\)', content)

    # Сканируем Frontend
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            # ПРОВЕРКА НА LOCALHOST (Твоя прошлая ошибка)
            if "127.0.0.1" in content or "localhost" in content:
                issues.append(f"{Colors.RED}❗ КРИТИЧЕСКАЯ ОШИБКА: В index.html найден 127.0.0.1. Бот не заработает на телефоне!{Colors.END}")
            
            # Ищем вызовы fetch
            logic["calls"] = re.findall(r'fetch\([\'\"`]?(?:\${API_URL})?([^?\'\"`\s]+)', content)

    # Сверяем эндпоинты
    for call in logic["calls"]:
        # Очищаем путь от переменных JS
        clean_call = re.sub(r'\${[^}]+}', '{id}', call).split('?')[0]
        match_found = False
        for api in logic["api"]:
            pattern = re.sub(r'\{[^}]+\}', '[^/]+', api)
            if re.fullmatch(pattern, clean_call) or clean_call in api:
                match_found = True
                break
        if not match_found and clean_call != "/":
            issues.append(f"{Colors.YELLOW}⚠️ ВНИМАНИЕ: Frontend вызывает {clean_call}, но в Backend такого эндпоинта нет!{Colors.END}")

    return logic, issues

def analyze_project():
    print(f'\n{Colors.CYAN}{"="*60}{Colors.END}')
    print(f'🚀 {Colors.CYAN}SAFESPACE ULTIMATE AUDIT{Colors.END} | {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
    print(f'{Colors.CYAN}{"="*60}{Colors.END}')
    
    # 1. СТАТУС СИСТЕМЫ
    print(f"\n📡 {Colors.CYAN}СИСТЕМНЫЙ СЛОЙ:{Colors.END}")
    print(f"   ∟ База данных: {get_db_stats()}")
    
    # 2. ПРОВЕРКА СВЯЗЕЙ
    print(f"\n🧠 {Colors.CYAN}АНАЛИЗ СВЯЗНОСТИ (BACKEND <-> FRONTEND):{Colors.END}")
    logic, issues = deep_scan_logic()
    
    if not issues:
        print(f"   {Colors.GREEN}✅ Все вызовы фронтенда подтверждены бэкендом.{Colors.END}")
    else:
        for issue in issues:
            print(f"   {issue}")

    # 3. ФИЗИЧЕСКАЯ СТРУКТУРА
    print(f"\n📁 {Colors.CYAN}СТРУКТУРА И ВЕС:{Colors.END}")
    skip = {'.git', '__pycache__', 'venv', 'env'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in skip]
        level = root.replace('.', '').count(os.sep)
        indent = '   ' * level
        print(f'{indent}📁 {os.path.basename(root) or "."}/')
        for f in files:
            f_path = os.path.join(root, f)
            size = os.path.getsize(f_path)
            s_str = f"{size}b" if size < 1024 else f"{size/1024:.1f}kb"
            print(f'{indent}   └── 📄 {f} ({s_str})')

    # 4. ГИТ
    print(f"\n📦 {Colors.CYAN}GIT СТАТУС:{Colors.END}")
    try:
        git_res = subprocess.check_output("git status -s", shell=True).decode()
        if git_res:
            print(f"   {Colors.YELLOW}📂 Есть незакоммиченные файлы. Пора сделать push!{Colors.END}")
        else:
            print(f"   {Colors.GREEN}✅ Чисто. Все изменения в репозитории.{Colors.END}")
    except: pass

    print(f'\n{Colors.CYAN}{"="*60}{Colors.END}')

if __name__ == "__main__":
    analyze_project()