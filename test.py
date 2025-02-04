from database import  get_connection
def remove_user(user_id):
    """Удаляет пользователя из базы данных"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM init_clients WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    print(f"🗑 Пользователь {user_id} удалён из базы данных.")



remove_user(user_id='357981474')