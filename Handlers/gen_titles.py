from Handlers import Buttons
import json
from Handlers import tg_parse
import editabs
from Init_client import *
import asyncio
from Handlers import processing
import aiocron
from aiog import *


async def gen_titles(callback_query):
    global generate_text, image_url, used_titles

    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    channels = editabs.get_user_channels(user_id)

    if not channels:  # Если список пуст

        return

    for channel in channels:
        try:
            messages = await tg_parse.parse(channel, days=1)

            if isinstance(messages, str):
                await bot.send_message(chat_id, messages, reply_markup=Buttons.get_inline_keyboard4())  # Отправляем пользователю сообщение об ошибке
                return
            else:
                seen_messages = set()
                selected_description = []

                for msg in messages:
                    if not msg.message.strip():
                        continue

                    link = f"{channel}/{msg.id}"
                    msg.message = await processing.compress_text(msg.message)
                    if msg.message not in seen_messages:
                        seen_messages.add(msg.message)
                        selected_description.append({
                            "message": msg.message,
                            "link": link
                            })

            selected_description_json = json.dumps(selected_description, ensure_ascii=False, indent=4)

                # try:
                #     print("Завершаем программу...")
                #     sys.exit(0)
                # except SystemExit:
                #     pass

        except Exception as e:
            await bot.send_message(chat_id, f"Ошибка при парсинге", reply_markup=Buttons.get_inline_keyboard3())

            continue


        history = editabs.get_chat_history(user_id, role = "assistant",title=1)


        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content":
                                            "\nОсновные правила для тебя:"
                                            "\nТы IT-блогер c многомиллионной аудиторией. Самый лучший. Тебе нельзя ошибаться. Твои подписчики ждут от тебя только самых интересных новостей"
                                            "Выяви из новостей, которые тебе придут, темы и в ответе пришли только темы"
                                            "Тебе придут новости в формате json '{message: text_news, link: url_news}' и накопленная история в json '{role: assistant, title: предыдущие темы}'"
                                            "Сравнивай каждую новую тему с предыдущей (из истории), если совпадают, то все равно присылай. Если тем в истории еще нет, "
                                            "то придумывай темы на основе новостей."
                                            "Пришли в ответе 5 тем.Отвечай по json_schema. Ссылки которые нужно прикрепить начинаются на https://t.me/"
                                            "К каждой новости прикреплены ссылки на них, когда выявишь 5 тем, обязательно прикрепи к каждой теме ссылку из какого канала ты взял тему для новости"
                                            "ДЛЯ ОДНОЙ ССЫЛКИ ОДНА ТЕМА"
                                            "Пришли в ответе 5 тем."
                                            "К каждой теме обязательно прикрепи текст новости"
                                            "Ты игнорируешь короткие посты, в которых мало текста, скорее всего это реклама или юмор. НЕ ДОБАВЛЯЕШЬ В ТЕМЫ"
                                            "Твой фокус внимания направлен только на научные и информативные статьи"
                                            "НИКОГДА не добавляй в темы новости которые могут содержать рекламу. Как правило, они помечены словом 'Реклама' "
                                            "Тебе придут новости из новостных каналов за неделю. Выяви самые интересные новости об IT-индустрии, тебе нужны новости только об искусственном интеллекте"
                                            "Различай названия каналов из ссылок ПРИМЕР: 'https://t.me/namechannel'"
                                            "НИКОГДА НЕ АНАЛИЗИРУЙ НОВОСТИ ДЛИНА КОТОРЫХ МЕНЬШЕ 50 СИМВОЛОВ"


                 },
                {"role": "user", "content": f"Description: {selected_description_json}, {history} \n\n Ты игнорируешь короткие посты,"
                                            " в которых мало текста, скорее всего это реклама или юмор НЕ ДОБАВЛЯЕШЬ В ТЕМЫ"
                                            "Твой фокус внимания направлен только на научные и информативные статьи" "К каждой теме обязательно прикрепи текст новости"
                                            "НИКОГДА НЕ АНАЛИЗИРУЙ НОВОСТИ ДЛИНА КОТОРЫХ МЕНЬШЕ 50 СИМВОЛОВ"}
                ],

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "titles",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "topics": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "title": {"type": "string"},
                                        "description":{"type":"string"},
                                        "url": {"type": "string"}
                                        },
                                    "required": ["id", "title","description", "url"],
                                    "additionalProperties": False
                                    }
                                }
                            },
                        "required": ["topics"],
                        "additionalProperties": False
                        },
                    "strict": True
                    }
                },
            temperature=0.4
            )

        response_json = json.loads(response.choices[0].message.content)



        for topic in response_json.get("topics", []):
            topic_id = topic["id"]
            title = topic["title"].strip()
            description = topic["description"].strip()
            url = topic.get("url", "").strip()

            editabs.save_chat_history(user_id, "assistant", topic_id, title, description, url)

        print(f"Обработан канал: {channel} и отправлен в GPT.")

        await asyncio.sleep(2)

    await bot.send_message(chat_id, "С парсингом я закончил", reply_markup=Buttons.get_inline_keyboard3())

