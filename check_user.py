import sqlite3
import os

def check_user_progress(user_id):
    db_path = 'safespace.db'
    if not os.path.exists(db_path):
        print("❌ База данных 'safespace.db' не найдена.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Поиск пользователя {user_id}...")
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()

        if user:
            print(f"✅ ПОЛЬЗОВАТЕЛЬ НАЙДЕН:")
            print(f"   🆔 ID: {user[0]}")
            print(f"   👤 Имя: {user[1]}")
            print(f"   🏔️ Текущий день: {user[2]}")
        else:
            print(f"⚠️ Пользователь {user_id} отсутствует в базе.")

    except Exception as e:
        print(f"🔥 Ошибка при чтении БД: {e}")

if __name__ == "__main__":
    # ID из вашего запроса
    check_user_progress(391491090)