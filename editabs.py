from pyexpat.errors import messages

from database import  get_connection
import json
import logging

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
    return result if result else []


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
    cursor.execute("DELETE FROM generalized_topics WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM subtopics WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def delete_gen_sub_top(user_id):

    """Удаляет историю сообщений только для указанного `user_id`"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM generalized_topics WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM subtopics WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()


def delete_all_history():


    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history")
    cursor.execute("DELETE FROM generalized_topics")
    cursor.execute("DELETE FROM subtopics")

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

def get_next_local_topic_id(user_id: int) -> int:
    """
    Возвращает следующий локальный ID темы для данного пользователя.
    Ищет максимальный topic_id и прибавляет 1.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Ищем максимальный topic_id у данного пользователя
    cursor.execute("""
        SELECT COALESCE(MAX(topic_id), 0)
        FROM generalized_topics
        WHERE user_id = ?
    """, (user_id,))
    max_topic_id = cursor.fetchone()[0]
    conn.close()

    return max_topic_id + 1  # Следующий номер


def save_top_subtop(response_json, user_id):
    """Сохраняет темы и подтемы в базу данных, продолжая нумерацию существующих subtopic_id"""
    conn = get_connection()
    cursor = conn.cursor()

    # Обработка основных тем
    for topic in response_json["topics"]:
        topic_id = topic["id"]  # Используем оригинальный id темы из JSON

        # Сохраняем обобщённую тему
        title = topic["title"]
        cursor.execute("""
                INSERT OR IGNORE INTO generalized_topics (user_id, topic_id, title)
               VALUES (?, ?, ?)
           """, (user_id, topic_id, title))

        # Получаем максимальный subtopic_id для этой темы у пользователя
        cursor.execute("""
            SELECT MAX(subtopic_id) FROM subtopics 
            WHERE user_id = ? AND general_topic_id = ?
        """, (user_id, topic_id))

        result = cursor.fetchone()
        max_subtopic_id = result[0] if result[0] is not None else 0

        # Определяем базу для prefix
        prefix = topic_id * 100  # Например, для general_topic_id=1 prefix=100

        # Обрабатываем подтемы
        for i, subtopic in enumerate(topic["subtopics"]):
            # Получаем данные
            original_subtopic_id = subtopic["id"]
            sub_title = subtopic["title"]

            # Проверяем, существует ли уже эта подтема
            cursor.execute("""
                SELECT COUNT(*) FROM subtopics 
                WHERE user_id = ? AND title = ? AND general_topic_id = ?
            """, (user_id, sub_title, topic_id))

            if cursor.fetchone()[0] == 0:
                # Если не существует, вычисляем новый subtopic_id
                if max_subtopic_id >= prefix and max_subtopic_id < prefix + 100:
                    # Если уже есть записи с правильным префиксом, продолжаем нумерацию
                    new_subtopic_id = max_subtopic_id + 1
                else:
                    # Начинаем с базового prefix + 1
                    new_subtopic_id = prefix + 1

                # Сохраняем подтему с новым id
                cursor.execute("""
                    INSERT INTO subtopics (subtopic_id, user_id, title, general_topic_id) 
                    VALUES (?, ?, ?, ?)
                """, (new_subtopic_id, user_id, sub_title, topic_id))

                # Обновляем max_subtopic_id
                max_subtopic_id = new_subtopic_id

    conn.commit()
    conn.close()



def get_top(user_id, gen_id=None):
    """Возвращает список тем и подтем для конкретного пользователя"""
    conn = get_connection()
    cursor = conn.cursor()

    if gen_id:
        cursor.execute("SELECT topic_id, title FROM generalized_topics WHERE user_id = ? AND topic_id = ?", (user_id, gen_id))
        topics = {row[0]: {"id": row[0], "title": row[1]} for row in cursor.fetchall()}
    else:
        cursor.execute("SELECT topic_id, title FROM generalized_topics WHERE user_id = ?", (user_id,))
        topics = {row[0]: {"id": row[0], "title": row[1], "subtopics": []} for row in cursor.fetchall()}

        cursor.execute("SELECT title, subtopic_id, general_topic_id  FROM subtopics WHERE user_id = ?", (user_id,))
        for row in cursor.fetchall():
            subtopic_id, title, general_topic_id = row
            if general_topic_id in topics:

                topics[general_topic_id]["subtopics"].append({"subtopic_id": subtopic_id, "title": title})
    conn.commit()
    conn.close()
    return list(topics.values())

def get_subtop(user_id, gen_id):
    """
    Получает подтемы для конкретного пользователя по ID общей темы (gen_id).
    Возвращает список подтем в формате [{"id": sub_id, "title": sub_title}, ...].
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Выбираем только подтемы, относящиеся к данной общей теме и пользователю
    cursor.execute("SELECT subtopic_id, title FROM subtopics WHERE user_id = ? AND general_topic_id = ?", (user_id, gen_id))
    subtopics = [{"subtopic_id": row[0], "title": row[1]} for row in cursor.fetchall()]

    conn.commit()
    conn.close()
    return subtopics


def get_selected_subtopics(user_id, subtopic_ids=None):
    """
    Получает список конкретных подтем для пользователя по их ID.

    :param user_id: ID пользователя.
    :param subtopic_ids: Список ID подтем (например, [101, 202, 501]).
    :return: Список подтем в формате [{"id": sub_id, "title": sub_title}, ...].
    """
    conn = get_connection()
    cursor = conn.cursor()
    if isinstance(subtopic_ids, str):
        subtopic_ids = list(map(int, subtopic_ids.split(",")))
    # Создаем плейсхолдеры для подстановки в SQL-запрос
    placeholders = ",".join(["?"] * len(subtopic_ids))

    # Запрос выбирает только указанные подтемы у данного пользователя
    query = f"SELECT subtopic_id, title FROM subtopics WHERE user_id = ? AND subtopic_id IN ({placeholders})"

    cursor.execute(query, [user_id] + subtopic_ids)
    subtopics = [{"subtopic_id": row[0], "title": row[1]} for row in cursor.fetchall()]

    conn.close()
    return subtopics


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

import sqlite3

def set_user_mode(user_id: int, mode: str):

    # Получаем соединение
    conn = get_connection()
    if conn is None:
        logging.error("Не удалось получить соединение с базой данных")
        return False

    cursor = conn.cursor()

    # Проверяем текущее значение режима
    cursor.execute("SELECT mode FROM user_modes WHERE user_id = ?", (user_id,))

    # Используем INSERT OR REPLACE для обновления существующей записи
    cursor.execute("""
            INSERT OR REPLACE INTO user_modes (user_id, mode)
            VALUES (?, ?)
        """, (user_id, mode))

    # Проверяем количество затронутых строк
    rows_affected = cursor.rowcount

    # Коммитим изменения
    conn.commit()
    conn.close()
    return True or False

def get_user_mode(user_id: int):

    try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT mode FROM user_modes WHERE user_id = ?
            """, (user_id,))

            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                # Если режим не установлен, возвращаем дефолтный 'ai'
                return

    except Exception as e:
        logging.error(f"Ошибка получения режима для пользователя {user_id}: {e}")
        return

def save_user_days(user_id: int, days: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_modes SET days = ? WHERE user_id = ?",
        (days, user_id)
    )
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO user_modes (user_id, days) VALUES (?, ?)",
            (user_id, days)
        )
    conn.commit()
    conn.close()

def get_user_days(user_id: int):

    try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT days FROM user_modes WHERE user_id = ?
            """, (user_id,))

            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                return 1

    except Exception as e:
        logging.error(f"Ошибка получения режима для пользователя {user_id}: {e}")
        return 1



# topics = get_top_subtop()
# print(json.dumps(topics, indent=4, ensure_ascii=False))


# title="Эффективность ChatGPT в психотерапии и проблемы обновления голосовых помощников Siri и Alexa на базе генеративного ИИ"
# topics_with_descriptions = {}

# ff = get_descriptions_by_title(title = "Создание и анимация 3D моделей с использованием нейросетевых технологий")
# print (ff)

# topics_with_descriptions.setdefault(title,ff)
# print (topics_with_descriptions)
#
#
