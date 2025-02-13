import asyncio
import json

import aiogram.enums

import editabs
from init_client import *
from . import buttons
from . import news as package_news
from handlers import processing, tg_parse
from aiog import *
import chat
import pandas
import states
import re


@dp.message(aiogram.F.text.lower() == "темы недели")
async def button_channels(message: aiogram.types.Message, state=None, text=None) -> None:
    user_id = message.from_user.id
    history = editabs.get_chat_history(user_id, role="assistant")
    df = pandas.DataFrame(history)
    df = df[df['title'] != 'НЕ ПО ТЕМЕ']
    counts = df['title'].value_counts()  # это Series, отсортированная по убыванию
    counts_dict = counts.to_dict()

    text = ("*Вот темы, о которых говорили за прошлую неделю:*\n"
            "_В скобках указано сколько раз эта тема повторилась в разных каналах_\n\n"
            "_Выберите на клавиатуре номера тем, по которым нужно сгенерировать новость_\n\n")
    for index, topic in enumerate(counts_dict.items(), start=1):
        text += f"{index}. {topic[0]} *[{topic[1]}]*\n"

    builder = InlineKeyboardBuilder()
    row = []
    for i in range(1, len(counts_dict)+1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=states.ChooseCallback(n=i, c=len(counts_dict), ch="").pack()))

        if i % 8 == 0:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))


    await message.answer(text, parse_mode=aiogram.enums.ParseMode.MARKDOWN, reply_markup=builder.as_markup())

    await message.delete()


@dp.callback_query(aiogram.F.data == "cancel_choose")
async def add_channel_request(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=callback.message.md_text,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        reply_markup=None)


@dp.callback_query(states.GenerateCallback.filter())
async def add_channel_request(callback: types.CallbackQuery):
    callback_data = states.GenerateCallback.unpack(callback.data)
    chosen = [int(x) for x in callback_data.choose.split(',') if x]

    selected_topics = []
    for line in callback.message.text.splitlines():
        match = re.match(r'^(\d+)\.\s*(.+)$', line)
        if match:
            num = int(match.group(1))
            topic_text = match.group(2)
            if num in chosen:
                selected_topics.append(f"{topic_text.rsplit('[')[0].strip()}")
    print(selected_topics)





@dp.callback_query(states.ChooseCallback.filter())
async def add_channel_request(callback: types.CallbackQuery):
    callback_data = states.ChooseCallback.unpack(callback.data)
    chosen = [int(x) for x in callback_data.ch.split(',') if x]

    if callback_data.n in chosen:
        chosen.remove(callback_data.n)
    else:
        chosen.append(callback_data.n)

    if len(chosen) > 5:
        await callback.answer(text="Максимальное количество тем - 5")
        return

    chosen.sort()
    chosen_str = ",".join(str(x) for x in chosen)

    builder = InlineKeyboardBuilder()
    row = []
    for i in range(1, callback_data.c + 1):
        if i in chosen:
            button_text = "✅"
        else:
            button_text = str(i)

        row.append(InlineKeyboardButton(text=button_text, callback_data=states.ChooseCallback(n=i, c=callback_data.c, ch=chosen_str).pack()))
        if i % 8 == 0:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))

    if len(chosen) > 0:
        builder.row(InlineKeyboardButton(text="Сгенерировать новость", callback_data=states.GenerateCallback(choose=chosen_str).pack()))

    await callback.message.edit_text(text=callback.message.md_text, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, reply_markup=builder.as_markup())


@dp.callback_query(aiogram.F.data.startswith("delete_topic_"))
async def delete_selected_topic(callback_query: types.CallbackQuery, state: FSMContext):

    topic_index = int(callback_query.data.split("_")[-1])

    user_data = await state.get_data()
    news = user_data.get("news", [])
    message_id = user_data.get("message_id")


    if topic_index < len(news):
        del news[topic_index]

    if not news:
        await callback_query.message.edit_text("Все темы удалены.")
        await state.clear()
        return

    #  Обновляем сообщение после удаления
    formatted_news = processing.escape_markdown_v2(news)

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=message_id,
        text=f"{formatted_news}",
        parse_mode="MarkdownV2",
        reply_markup=buttons.get_delete_keyboard(news),
        disable_web_page_preview=True
    )

    await state.update_data(formatted_news=formatted_news)


@dp.callback_query(lambda c: c.data == "confirm_topics")
async def confirm_topics(callback_query: types.CallbackQuery, state: FSMContext):
    """Окончательное подтверждение тем"""
    user_data = await state.get_data()
    news = user_data.get("news", [])

    formatted_news = processing.escape_markdown_v2(news)

    await callback_query.message.edit_text(
        f"Итоговый список тем:\n\n{formatted_news}",
        parse_mode="MarkdownV2", reply_markup=buttons.confirm_keyboard5(),
        disable_web_page_preview=True
    )

    await state.update_data(pending_function=package_news.generate_news, formatted_news=formatted_news)


    # await state.clear()  #  Очищаем state после завершения



@dp.callback_query(aiogram.F.data == "generate")
async def top_titles(callback_query, state: FSMContext):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    history  = editabs.get_chat_history(user_id,role="assistant", title=1)

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Выяви из этих заголовков часто повторяющиеся. В ответе предоставь title и url"
             },
            {"role": "user", "content": f"Description: {history}\n\n Выяви из этих заголовков часто повторяющиеся и в ответе предоставь топ 5 по убыванию.  В ответе предоставь title и url"}
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
                                    "url": {"type": "string"}
                                    },
                                "required": ["id", "title",  "url"],
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

    topics_with_descriptions = json.dumps([
        {
            "id": topic.get("id"),
            "title": topic.get("title"),
            "url": topic.get("url"),
            "description": editabs.get_description_by_url(topic.get("url", "")) or "Описание не найдено"
            }
        for topic in response_json.get("topics", [])
        ], ensure_ascii=False, indent=4)


    json_news = json.loads(topics_with_descriptions)

    news = processing.escape_markdown_v2(json_news)

    await state.update_data(news=json_news, message_id=message_id)

    # await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())
    await bot.edit_message_text(chat_id=chat_id,
                                message_id=message_id, text=news, parse_mode="MarkdownV2", reply_markup=buttons.get_delete_keyboard(json_news), disable_web_page_preview=True)



async def gen_titles_for_titles(channel_link, chat_id):
    messages = await tg_parse.parse(channel_link, days=7)
    if isinstance(messages, str):
        await bot.send_message(chat_id, messages)
        return
    else:
        seen_messages = set()
        selected_description = []

        for msg in messages:
            if not msg.message.strip():
                continue

            link = f"{channel_link}/{msg.id}"
            msg.message = await processing.compress_text(msg.message)
            if msg.message not in seen_messages:
                seen_messages.add(msg.message)
                selected_description.append({
                    "message": msg.message,
                    "link": link
                    })

    for description in selected_description:

        history = editabs.get_chat_history(chat_id, role ="assistant", title=1)

        chat_messages = chat.MessageHistory().add_message(
            role=chat.Message.ROLE_SYSTEM,
            content=f"Ты получишь текста поста, твоя задача выделить основную тему для него, она должна "
                    f"содержать в себе основные сущности о которых идет речь.\nЕсть список уже существующих тем: {history}.\n"
                    f"Если текст поста подходит под одну из этих тем - выбери ее, а не придумывай новую."
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
        editabs.save_chat_history(chat_id, "assistant", topic_id, title, text, url)

        print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")

