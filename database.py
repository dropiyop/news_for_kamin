import sqlite3

# Имя файла базы данных
DB_FILE = r"C:\NewsforKamin\pythonProject\FILE.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn


# Инициализация базы данных
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    #
    # cursor.execute("""
    #     DROP TABLE generalized_topics
    #     """)
    #
    # cursor.execute("""
    #         DROP TABLE subtopics
    #         """)
    #
    # cursor.execute("""
    #                 DROP TABLE chat_history
    #                 """)

    # cursor.execute("""
    #         DROP TABLE user_channels
    #         """)
    #


    # Таблица для хранения каналов пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_channels (
            user_id INTEGER,
            channel TEXT,
            channel_name TEXT,
            PRIMARY KEY (user_id, channel)
        )
    """)



    # Таблица для инициализированных клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS init_clients (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT,
            contact_username TEXT,
            contact_name TEXT,
            contact_phone TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(init_clients)")
    columns = [row[1] for row in cursor.fetchall()]

    # Если `chat_id` отсутствует — добавляем
    if "chat_id" not in columns:
        cursor.execute("ALTER TABLE init_clients ADD COLUMN chat_id INTEGER")



    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
        topic_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        url TEXT
    )
    """)


    # Таблица общих тем
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS generalized_topics (
            global_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL, 
            title TEXT NOT NULL,                  
            UNIQUE(user_id, topic_id)                     

           )
       """)

    # Таблица подтем
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS subtopics (
               global_id INTEGER PRIMARY KEY AUTOINCREMENT,
               subtopic_id  INTEGER  NOT NULL,
               user_id INTEGER NOT NULL,
               title TEXT NOT NULL,
               general_topic_id INTEGER  NOT NULL,  -- ID общей темы (связь)
               FOREIGN KEY (general_topic_id) REFERENCES generalized_topics(topic_id)
           )
       """)




    conn.commit()
    conn.close()

# Инициализируем базу данных
init_db()

