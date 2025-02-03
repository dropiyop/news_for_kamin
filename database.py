import sqlite3

# Имя файла базы данных
DB_FILE = "FILE.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn


# Инициализация базы данных
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица для хранения каналов пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_channels (
            user_id INTEGER,
            channel TEXT,
            PRIMARY KEY (user_id, channel)
        )
    """)

    # Таблица для хранения использованных заголовков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS used_titles (
            user_id INTEGER,
            title TEXT,
            PRIMARY KEY (user_id, title)
        )
    """)

    # Таблица для инициализированных клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS init_clients (
            user_id INTEGER PRIMARY KEY,
            contact_username TEXT,
            contact_name TEXT,
            contact_phone TEXT
        )
    """)

    conn.commit()
    conn.close()

# Инициализируем базу данных
init_db()