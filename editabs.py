from pyexpat.errors import messages

from database import  get_connection



def add_user_channel(user_id, channel):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO user_channels (user_id, channel) VALUES (?, ?)", (user_id, channel))
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

def get_user_channels(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT channel FROM user_channels WHERE user_id = ?", (user_id,))
    channels = [row[0] for row in cursor.fetchall()]
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


def remove_user(user_id):
    """Удаляет пользователя из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM init_clients WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print(f"🗑 Пользователь {user_id} удалён из базы данных.")




def get_chat_history(user_id, role = None, title = None):
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
    """Сохраняет историю сообщений пользователя в базе"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO chat_history (user_id, role, topic_id, title, description, url)
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


# ff = get_chat_history(user_id='357981474', role = "assistant", title=1)
# print (ff)
#

