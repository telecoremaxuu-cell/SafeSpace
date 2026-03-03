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
    """Проверка, запущен ли сервер на самом деле"""
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

        info_parts = []
        if 'users' in tables:
            cursor.execute("SELECT count(*) FROM users")
            u_count = cursor.fetchone()[0]
            info_parts.append(f"Юзеров: {u_count}")

        if 'tasks' in tables:
            cursor.execute("SELECT count(*) FROM tasks")
            t_count = cursor.fetchone()[0]
            info_parts.append(f"Заданий: {t_count}")

        info_parts.append(f"Таблицы: {', '.join(tables)}")
        conn.close()
        return f"{Colors.GREEN}✅ OK{Colors.END} ({'; '.join(info_parts)})"
    except Exception as e: return f"{Colors.YELLOW}⚠️ Ошибка БД: {e}{Colors.END}"

def deep_scan_recursive():
    issues = []
    fixed_files = []
    logic = {"api": [], "calls": []}
    
    # Рекурсивный обход ВСЕГО проекта
    for root, dirs, files in os.walk('.'):
        # Пропускаем только тяжелый системный мусор
        if any(part in root for part in ['.git', '__pycache__', 'venv', 'env', 'node_modules']):
            continue
            
        for file in files:
            path = os.path.join(root, file)
            
            # 1. Лечим BOM везде, где найдем
            if file.endswith(('.py', '.html', '.js', '.css', '.env')):
                if fix_bom(path):
                    fixed_files.append(path)

            # 2. Анализ Python файлов (Backend логика)
            if file.endswith('.py'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Собираем ВСЕ эндпоинты проекта
                        logic["api"].extend(re.findall(r'@app\.(?:get|post|put|delete)\("([^"]+)"\)', content))
                        
                        # Проверка авто-регистрации (в любом файле)
                        if "main.py" in file and "db.add" not in content:
                             issues.append(f"{Colors.RED}❗ ЛОГИКА: В {file} не найдена база/регистрация!{Colors.END}")
                except: pass

            # 3. Анализ Frontend файлов (JS/HTML)
            if file.endswith(('.html', '.js')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Ищем все вызовы API
                        logic["calls"].extend(re.findall(r'fetch\([\'\"`]?(?:\${API_URL})?([^?\'\"`\s]+)', content))
                        
                        # Проверка на localhost
                        if "127.0.0.1" in content or "localhost" in content:
                            issues.append(f"{Colors.RED}❗ СЕТЬ: Localhost найден в {path}!{Colors.END}")
                except: pass

    # 4. Проверка активного порта
    if not check_port(8000):
        issues.append(f"{Colors.YELLOW}⚠️ СЕРВЕР: Порт 8000 молчит. Uvicorn не запущен!{Colors.END}")

    # Сверка эндпоинтов (глобальная)
    for call in logic["calls"]:
        clean_call = re.sub(r'\${[^}]+}', '{id}', call).split('?')[0]
        if not any(re.fullmatch(re.sub(r'\{[^}]+\}', '[^/]+', api), clean_call) or clean_call in api for api in logic["api"]):
            if clean_call != "/" and not clean_call.startswith('http') and not clean_call.startswith('.'):
                issues.append(f"{Colors.YELLOW}⚠️ СИНХРО: Фронт требует {clean_call}, но в API его нет!{Colors.END}")

    return logic, issues, fixed_files

def analyze_project():
    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')
    print(f'🚀 {Colors.WHITE}SAFESPACE TOTAL CONTROL v7.0{Colors.END} | {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
    print(f'{Colors.PURPLE}{"#"*60}{Colors.END}')
    
    # 1. БД
    print(f"\n📡 {Colors.CYAN}СИСТЕМНЫЙ СЛОЙ (БАЗА):{Colors.END}")
    print(f"   ∟ {get_db_stats()}")
    
    # 2. ГЛОБАЛЬНЫЙ АНАЛИЗ
    print(f"\n🧠 {Colors.CYAN}АНАЛИЗ ВСЕЙ СТРУКТУРЫ:{Colors.END}")
    logic, issues, fixed = deep_scan_recursive()
    
    if fixed:
        for f in fixed:
            print(f"   {Colors.GREEN}🛠 ИСПРАВЛЕНО: Убран BOM из {f}{Colors.END}")
    
    if not issues:
        print(f"   {Colors.GREEN}✅ Все файлы синхронизированы и чисты.{Colors.END}")
    else:
        for issue in issues:
            print(f"   {issue}")

    # 3. ПОЛНАЯ КАРТА ПРОЕКТА (Твоя версия)
    print(f"\n📁 {Colors.CYAN}ПОЛНАЯ КАРТА ПРОЕКТА:{Colors.END}")
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

    # 4. GIT
    print(f"\n📦 {Colors.CYAN}GIT СТАТУС:{Colors.END}")
    try:
        git_res = subprocess.check_output("git status -s", shell=True).decode()
        print(f"   {Colors.YELLOW}📂 Есть незакоммиченные файлы.{Colors.END}" if git_res else f"   {Colors.GREEN}✅ Чисто.{Colors.END}")
    except:
        print(f"   {Colors.RED}❌ Git Error{Colors.END}")

    print(f'\n{Colors.PURPLE}{"#"*60}{Colors.END}')

if __name__ == "__main__":
    analyze_project()