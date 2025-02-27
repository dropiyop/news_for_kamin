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


async def shedule_title():


    user_ids = editabs.get_all_user_ids()
    print(user_ids)

    for user_id in user_ids:

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

                chat_messages = chat.MessageHistory().add_message(
                    role=chat.Message.ROLE_SYSTEM,
                    content=f"Ты получишь текст поста, твоя задача выделить основную тему для него"
                            f"содержать в себе конкретные сущности о которых идет речь, выделяй тему не по первым словам, а по всему тексту новости, "
                            f"НЕ ИСПОЛЬЗУЙ НИКАКИЕ ЗНАКИ ПРЕПИНАНИЯ"
                            f"Посты с #Реклама игнорируй"
                            f"придумывай подробную тему и уникальную тему.\nЕсть список уже существующих тем: {history}.\n"
                            f"Если текст поста подходит под одну из этих тем, то есть содержит в себе такие же конкретные сущности о которых идет речь  - выбери ее, а не придумывай новую."
                            f"Если пост отличается от темы, придумай новую."
                            f"НИКОГДА НЕ АНАЛИЗИРУЙ НОВОСТИ ДЛИНА КОТОРЫХ МЕНЬШЕ 50 СИМВОЛОВ.\n\n"
                            f"ТЕМА ДОЛЖНА ОТНОСИТЬСЯ К СФЕРЕ НЕЙРОННЫХ СЕТЕЙ, ИСКУССТВЕННОГО ИНТЕЛЛЕКТА И ПОДОБНОГО. "
                            f"ЕСЛИ ПОСТ НЕ ОТНОСИТСЯ К ЭТОЙ ТЕМАТИКЕ, ВЕРНИ ТЕМУ С НАЗВАНИЕМ 'НЕ ПО ТЕМЕ'").add_message(
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
    scheduler = apscheduler.schedulers.asyncio.AsyncIOScheduler()

    scheduler.add_job(
        shedule_title,
        apscheduler.triggers.cron.CronTrigger(hour=0, minute=3),
        misfire_grace_time=300,
        id="parse_channel"
    )

    print(f"Планировщик запущен на каждый день 00:03")

    scheduler.start()

#
# async def scheduled_task():
#     print("Запускаю `shedule_title()` в 00:01...")
#     await shedule_title()
#
#

