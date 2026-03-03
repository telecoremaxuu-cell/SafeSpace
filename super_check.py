import os
import sqlite3
import re

def check_project():
    print("="*60)
    print("🚀 ТОТАЛЬНАЯ ПРОВЕРКА SAFESPACE v1.0")
    print("="*60)

    # 1. ПРОВЕРКА БАЗЫ ДАННЫХ
    db_path = "E:/SafeSpace/safespace.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            tasks_count = cursor.fetchone()[0]
            print(f"✅ БАЗА: Найдено {tasks_count} заданий.")
            
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"📊 КОЛОНКИ В ТАБЛИЦЕ TASKS: {columns}")
            conn.close()
        except Exception as e:
            print(f"❌ БАЗА ОШИБКА: {e}")
    else:
        print("❌ БАЗА: Файл safespace.db не найден!")

    # 2. ПРОВЕРКА MAIN.PY (CORS И ПУТИ)
    main_path = "E:/SafeSpace/backend/main.py"
    if os.path.exists(main_path):
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "CORSMiddleware" in content:
                print("✅ BACKEND: CORS настроен (защита от блокировок).")
            else:
                print("⚠️ BACKEND: CORS НЕ НАЙДЕН! Это может блокировать запросы.")
            
            if "app.get(\"/api/tasks/{task_id}\")" in content or "app.get('/api/tasks/{task_id}')" in content:
                print("✅ BACKEND: Эндпоинт /api/tasks/{task_id} прописан.")
            else:
                print("⚠️ BACKEND: Эндпоинт для заданий не найден или имеет другой путь!")

    # 3. ПРОВЕРКА INDEX.HTML (ССЫЛКА API)
    index_path = "E:/SafeSpace/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            api_match = re.search(r'const API_URL\s*=\s*["\'](https?://.*?)["\']', content)
            if api_match:
                url = api_match.group(1)
                print(f"🌐 FRONTEND: Настроен на URL: {url}")
                if "localhost" in url or "127.0.0.1" in url:
                    print("⚠️ ВНИМАНИЕ: Ссылка ведет на localhost. На телефоне работать НЕ БУДЕТ!")
                else:
                    print("✅ FRONTEND: Используется внешняя ссылка (Ngrok).")
            else:
                print("❌ FRONTEND: Переменная API_URL не найдена!")

    # 4. ПРОВЕРКА ПОРТА 8000
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    if result == 0:
        print("✅ СЕРВЕР: Порт 8000 открыт (Uvicorn запущен).")
    else:
        print("❌ СЕРВЕР: Порт 8000 закрыт! (Uvicorn НЕ ЗАПУЩЕН).")
    sock.close()

    print("="*60)
    print("Сделай скриншот этого вывода или скопируй его сюда.")

if __name__ == "__main__":
    check_project()