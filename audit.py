import os
import re
import sqlite3
import requests
import subprocess
from datetime import datetime

def get_db_stats():
    """Проверяет состояние базы данных"""
    db_path = 'safespace.db'
    if not os.path.exists(db_path):
        return "❌ БАЗА НЕ СОЗДАНА"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return f"✅ OK (Пользователей в базе: {count})"
    except Exception as e:
        return f"⚠️ Ошибка базы: {e}"

def check_env_health():
    """Проверяет полноту настроек в .env"""
    required = ['TELEGRAM_BOT_TOKEN', 'WEBAPP_URL', 'DATABASE_URL']
    missing = []
    if not os.path.exists('.env'): return "❌ ФАЙЛ .env ОТСУТСТВУЕТ"
    with open('.env', 'r') as f:
        content = f.read()
        for key in required:
            if key not in content or len(content.split(f"{key}=")[1].strip()) < 5:
                missing.append(key)
    return "✅ OK" if not missing else f"⚠️ ПУСТЫЕ ПОЛЯ: {', '.join(missing)}"

def analyze_project():
    print(f'--- 🚀 SAFESPACE: ULTRA AUDIT [{datetime.now().strftime("%H:%M:%S")}] ---')
    
    # 1. СТАТУС СИСТЕМЫ
    print("\n📊 СОСТОЯНИЕ СИСТЕМЫ:")
    print(f"   ∟ База данных:    {get_db_stats()}")
    print(f"   ∟ Конфиг (.env):  {check_env_health()}")
    
    # 2. ПРОВЕРКА КОДА НА ЛОВУШКИ
    print("\n🔍 АНАЛИЗ КОДА:")
    checks = {
        'index.html': [
            (r'const\s+API_URL\s*=\s*".*127\.0\.0\.1.*"', "⚠️ API_URL смотрит на localhost! На телефоне не откроется."),
            (r'твой-логин', "⚠️ В ссылке GitHub остался 'твой-логин'!")
        ],
        'bot.py': [
            (r'WEBAPP_URL\s*=\s*".*твой-логин.*"', "⚠️ Бот шлет юзеров на несуществующий домен!")
        ],
        'backend/main.py': [
            (r'allow_origins=\["\*"\]', "✅ CORS настроен (доступ открыт)")
        ]
    }

    for file, patterns in checks.items():
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern, msg in patterns:
                    if re.search(pattern, content):
                        print(f"   [{file}] {msg}")
        else:
            print(f"   ❌ Файл {file} не найден!")

    # 3. ГИТ-КОНТРОЛЬ (Не забыл ли ты сделать PUSH?)
    print("\n📦 ГИТ-КОНТРОЛЬ:")
    try:
        status = subprocess.check_output("git status", shell=True).decode()
        if "branch is ahead" in status:
            print("   ⚠️ ВНИМАНИЕ: У тебя есть локальные коммиты. Сделай 'git push'!")
        elif "nothing to commit" in status:
            print("   ✅ Все изменения сохранены и отправлены.")
        else:
            print("   📂 Есть незакоммиченные изменения (сделай git add/commit).")
    except:
        print("   ❌ Git не найден.")

    print('\n' + '='*50)

if __name__ == "__main__":
    analyze_project()