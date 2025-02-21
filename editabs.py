from pyexpat.errors import messages

from database import  get_connection



def add_user_channel(user_id, channel, channel_name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO user_channels (user_id, channel, channel_name) VALUES (?, ?, ?)", (user_id, channel, channel_name))
    conn.commit()
    conn.close()

def remove_user_channel(user_id, channel):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("DELETE FROM user_channels WHERE user_id = ? AND channel = ?", (user_id, channel))
    conn.commit()
    conn.close()

def all_remove_channels(user_id):

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_channels WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_user_ids():
    """Получает всех пользователей из таблицы `user_channels`"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT user_id FROM user_channels")

    user_ids = [row[0] for row in cursor.fetchall()]

    conn.commit()
    conn.close()
    return user_ids

def get_user_url_channel(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT channel FROM user_channels WHERE user_id = ?", (user_id,))
    channels = cursor.fetchall()
    conn.close()
    return channels

def get_user_channels(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT channel, channel_name FROM user_channels WHERE user_id = ?", (user_id,))
    channels = cursor.fetchall()
    conn.close()
    return channels

def add_init_client(user_id,chat_id,contact_username,contact_name,contact_phone):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
          INSERT OR IGNORE INTO init_clients (user_id, chat_id, contact_username, contact_name, contact_phone) 
          VALUES (?, ?, ?, ?, ?)
      """, (user_id, chat_id, contact_username, contact_name, contact_phone))

    conn.commit()
    conn.close()

def get_client_user_id(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM init_clients WHERE user_id = ?", (user_id,))

    result = cursor.fetchone()  # Возвращает одну строку, если она существует

    conn.close()

    # Если результат найден, возвращаем user_id, иначе None
    return result[0] if result else None


def get_client_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM init_clients")

    result = cursor.fetchall()

    conn.close()

    # Если результат найден, возвращаем user_id, иначе None
    return result if result else None


def remove_user(user_id):
    """Удаляет пользователя из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM init_clients WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print(f"🗑 Пользователь {user_id} удалён из базы данных.")

def get_descriptions_by_title(title):
    """Ищет описания по заголовкам в `chat_history`"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT title, description, url FROM chat_history WHERE title LIKE ?"
    cursor.execute(query, (f"%{title}%",))

    descriptions =[ {'description':row[1], 'url': row[2]} for row in cursor.fetchall()]

    conn.commit()
    conn.close()
    return descriptions

def delete_chat_history(user_id):

    """Удаляет историю сообщений только для указанного `user_id`"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()



def get_chat_history(user_id = None, role = None, title = None):
    """Получает историю сообщений пользователя из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()


    if role:
        cursor.execute("""
                SELECT role, topic_id, title, description, url 
                FROM chat_history 
                WHERE user_id = ? AND role = ? 
                ORDER BY id ASC
            """, (user_id, role))
    else:
        cursor.execute("""
                SELECT role, topic_id, title, description, url 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY id ASC
            """, (user_id,))
    if title:
        titles = [
            {
            "title": row[2],
            "url": row[4]
            } for row in cursor.fetchall() if row[0] is not None]
        conn.close()
        return titles

    else:
        # Преобразуем результат в список словарей
        messages = [
            {
                "role": row[0],
                "topic_id": row[1],
                "title": row[2],
                "description": row[3],
                "url": row[4]
                } for row in cursor.fetchall()
            ]

        conn.close()
        return messages # Возвращает список сообщений



def save_chat_history(user_id, role, topic_id, title, description, url):
    """Сохраняет историю сообщений пользователя в базе. Если url уже существует у данного пользователя, не добавляет повторно."""
    conn = get_connection()
    cursor = conn.cursor()

    # Проверяем, есть ли запись с таким url у данного пользователя
    cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ? AND url = ?", (user_id, url))
    count = cursor.fetchone()[0]

    if count == 0:
        # Если у пользователя нет такой записи, добавляем её
        cursor.execute("""
            INSERT INTO chat_history (user_id, role, topic_id, title, description, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, role, topic_id, title, description, url))
        conn.commit()

    conn.close()



def get_description_by_url(url):
    """Ищет `description` в `chat_history` по `url`."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT description FROM chat_history WHERE url = ? LIMIT 1
    """, (url,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None



# title="Эффективность ChatGPT в психотерапии и проблемы обновления голосовых помощников Siri и Alexa на базе генеративного ИИ"
# topics_with_descriptions = {}
# ff = get_descriptions_by_title(title)
# topics_with_descriptions.setdefault(title,ff)
# print (topics_with_descriptions)
#
#
