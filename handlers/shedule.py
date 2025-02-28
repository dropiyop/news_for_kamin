import json
from pydoc_data.topics import topics

import apscheduler
from .topics import top_themes
from handlers import tg_parse
import editabs
from init_client import *
from handlers import processing
import chat
import  apscheduler.schedulers.asyncio
import apscheduler.triggers.cron
import pandas

async def shedule_title():


    user_ids = editabs.get_all_user_ids()
    print(user_ids)

    for user_id in user_ids:
        print(user_id)
        channels = editabs.get_user_url_channel(user_id)

        channels = [channel[0] for channel in channels]

        for channel in channels:
            print(channel)
            messages = await tg_parse.parse(channel, days=1)
            if isinstance(messages, str):
                await bot.send_message(user_id, messages)
                return


            else:
                seen_messages = set()
                selected_description = []

                for msg in messages:
                    if not msg.message.strip():
                        continue

                    link = f"{channel}/{msg.id}"
                    # msg.message = await processing.compress_text(msg.message)
                    if msg.message not in seen_messages:
                        seen_messages.add(msg.message)
                        selected_description.append({
                            "message": msg.message,
                            "link": link
                            })

            for description in selected_description:

                history = editabs.get_chat_history(user_id, role ="assistant", title=1)
                df = pandas.DataFrame(history)

                if 'title' in df.columns:
                    counts = df['title'].unique()
                else:
                    counts = []

                print(counts)

                chat_messages = chat.MessageHistory().add_message(
                    role=chat.Message.ROLE_SYSTEM,
                    content=f"Твоя задача - определить основную тему поста о нейронных сетях и искусственном интеллекте. \n" \
                            f"Тема должна отражать конкретные сущности, о которых идет речь в тексте, анализируй весь контент, а не только первые слова, \n" \
                            f"НЕ ИСПОЛЬЗУЙ ЗНАКИ ПРЕПИНАНИЯ, избегай слов-клише 'Новое', 'Оптимизация', 'Улучшения', 'Обновления', \n" \
                            f"формулируй подробную  тему. Если в новости упоминается конкретный продукт, группируй их в одну тему. \n" \
                            f"Примеры хороших тем: 'Улучшения в нейросетевых моделях на примере GPT-4.5', 'Тренды и навыки в ML-инженерии на 2025 год', \n" \
                            f"'Интеграция ChatGPT в образовательные учреждениях для учеников старших классов'. \n" \
                            f"Игнорируй посты с хэштегом #Реклама, НЕ анализируй тексты короче 50 символов, \n" \
                            f"если пост не относится к ИИ или нейросетям, верни 'НЕ ПО ТЕМЕ'. \n" \
                            f"Сверься со списком существующих тем: {counts}, \n" \
                            f"если текст подходит под существующую тему (содержит те же сущности или упоминает тот же продукт), используй ее, \n" \
                            f"если текст значительно отличается, создай новую тему.").add_message(
                    role=chat.Message.ROLE_USER,
                    content=f"{description['message']}")

                response = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=chat_messages.to_api_format(),
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "titles",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"}
                                },
                                "required": ["title"],
                                "additionalProperties": False
                                },
                            "strict": True
                            }
                        },
                    temperature=0.4
                    )

                response_json = json.loads(response.choices[0].message.content)


                topic_id = 1
                title = response_json.get("title").strip()
                text = description['message']
                url = description['link']
                editabs.save_chat_history(user_id, "assistant", topic_id, title, text, url)

                print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")

        await top_themes(user_id)

    user_id = "357981474"
    await bot.send_message(chat_id=user_id,text="Я нашел новости по расписанию")



def prepare_schedulers():
    scheduler_parse = apscheduler.schedulers.asyncio.AsyncIOScheduler()

    scheduler_parse.add_job(
        shedule_title,
        apscheduler.triggers.cron.CronTrigger(hour=0, minute=3),
        misfire_grace_time=300,

        id="parse_channel"
    )

    print(f"Планировщик запущен на каждый день")
    scheduler_parse.start()


def delete_history():
    scheduler_delete = apscheduler.schedulers.asyncio.AsyncIOScheduler()

    scheduler_delete.add_job(
        editabs.delete_all_history,
        apscheduler.triggers.cron.CronTrigger(
            day_of_week='sat',
            hour=23,
            minute=59,
        ),
        misfire_grace_time=300,
        id="delete"
    )

    print(f"Планировщик удаления запущен на ближайшую субботу в 23:59")
    scheduler_delete.start()

# async def scheduled_task():
#     print("Запускаю `shedule_title()` в 00:01...")
#     await shedule_title()
#
#

