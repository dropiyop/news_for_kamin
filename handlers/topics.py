import asyncio
import json

import aiogram.enums

import editabs
from init_client import *
from . import buttons, processing, tg_parse, news
from . import news as package_news
# from handlers import processing, tg_parse, news
from aiog import *
import chat
import pandas
import states
import re





@dp.message(aiogram.F.text.lower() == "темы недели")
async def button_channels(message: aiogram.types.Message) -> None:
    user_id = message.from_user.id
    history = editabs.get_chat_history(user_id, role="assistant")
    if not history:
        await bot.send_message(chat_id=user_id, text="А тем нет:(",reply_markup=buttons.parse_sevendays())
    else:
        df = pandas.DataFrame(history)
        df = df[df['title'] != 'НЕ ПО ТЕМЕ']
        counts = df['title'].value_counts()
        counts_dict = counts.to_dict()

        await send_topics_page(message, counts_dict, page=0)


async def send_topics_page(message, count_dict, page=0, chosen=None):
    if chosen is None:
        chosen = []  # список выбранных тем

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size else 0)

    start_idx = page * page_size
    end_idx = start_idx + page_size
    topics_page = list(count_dict.items())[start_idx:end_idx]

    text = ("*Вот темы, о которых говорили за прошлую неделю:*\n"
            "_В скобках указано сколько раз эта тема повторилась в разных каналах_\n\n"
            "_Выберите на клавиатуре номера тем, по которым нужно сгенерировать новость_\n\n")

    builder = InlineKeyboardBuilder()
    row = []

    # Формируем кнопки для каждой темы на текущей странице
    for index, (title, count) in enumerate(topics_page, start=start_idx + 1):
        # Если тема выбрана, можно отметить её галочкой
        button_text = "✅" if index in chosen else str(index)
        text += f"{index}. {title} *[{count}]*\n"
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=states.ChooseCallback(
                n=index,
                c=len(count_dict),
                ch=",".join(map(str, chosen)),
                page=page
            ).pack()
        ))
        # Разбиваем ряды по 8 кнопок (можно настроить под себя)
        if (index - start_idx) % 8 == 0:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    # Формирование навигационных кнопок с использованием собственного callback:
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="Назад",
            callback_data=states.NumberPageCallback(
                page=page - 1,
                choose=",".join(map(str, chosen))
            ).pack()
        ))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=page + 1,
                choose=",".join(map(str, chosen))
            ).pack()
        ))
    if navigation_buttons:
        builder.row(*navigation_buttons)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))

    await message.answer(text, parse_mode=aiogram.enums.ParseMode.MARKDOWN, reply_markup=builder.as_markup())
    await message.delete()



@dp.callback_query(aiogram.F.data == "cancel_choose")
async def add_channel_request(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        text=callback.message.md_text,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        reply_markup=None)
    selected_topics_per_user[user_id] = []


# @dp.callback_query(lambda c: c.data.startswith("page_"))
# async def change_page(callback: types.CallbackQuery):
#     """Обработчик кнопок '⬅ Назад' и 'Вперёд ➡'"""
#     user_id = callback.from_user.id
#     history = editabs.get_chat_history(user_id, role="assistant")
#
#     if not history:
#         await callback.message.edit_text("А тем нет :(", reply_markup=buttons.parse_sevendays())
#         return
#
#     df = pandas.DataFrame(history)
#     df = df[df['title'] != 'НЕ ПО ТЕМЕ']
#     counts_dict = df['title'].value_counts().to_dict()
#
#     page = int(callback.data.split("_")[1])
#     await send_topics_page(callback.message, counts_dict, page=page)
#




selected_topics_per_user = {}

@dp.callback_query(states.NumberPageCallback.filter())
async def navigate_page(callback: types.CallbackQuery, callback_data: states.NumberPageCallback):
    new_page = callback_data.page

    # Преобразуем строку с выбранными темами в список целых чисел
    chosen = [int(x) for x in callback_data.choose.split(",") if x]

    user_id = callback.from_user.id
    history = editabs.get_chat_history(user_id, role="assistant")
    if not history:
        await bot.send_message(
            chat_id=user_id,
            text="А тем нет:(",
            reply_markup=buttons.parse_sevendays()
        )
        return

    df = pandas.DataFrame(history)
    df = df[df['title'] != 'НЕ ПО ТЕМЕ']
    counts = df['title'].value_counts()
    count_dict = counts.to_dict()

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size != 0 else 0)
    start_idx = new_page * page_size
    topics_page = list(count_dict.items())[start_idx:start_idx + page_size]

    builder = InlineKeyboardBuilder()
    row = []
    text = ("*Вот темы, о которых говорили за прошлую неделю:*\n"
            "_В скобках указано сколько раз эта тема повторилась в разных каналах_\n\n"
            "_Выберите на клавиатуре номера тем, по которым нужно сгенерировать новость_\n\n")
    for global_index, (title, count) in enumerate(topics_page, start=start_idx + 1):
        button_text = "✅" if global_index in chosen else str(global_index)
        text += f"{global_index}. {title} *[{count}]*\n"
        data = states.ChooseCallback(
            n=global_index,
            c=len(count_dict),
            ch=",".join(map(str, chosen)),
            page=new_page
        ).pack()
        row.append(InlineKeyboardButton(text=button_text, callback_data=data))
        if (global_index - start_idx) % 8 == 0:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))
    if chosen:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=states.GenerateCallback(choose=",".join(map(str, chosen))).pack()
        ))

    navigation_buttons = []
    if new_page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="Назад",
            callback_data=states.NumberPageCallback(
                page=new_page - 1,
                choose=",".join(map(str, chosen))
            ).pack()
        ))
    if new_page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=new_page + 1,
                choose=",".join(map(str, chosen))
            ).pack()
        ))
    if navigation_buttons:
        builder.row(*navigation_buttons)

    await callback.message.edit_text(
        text=text,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN,
        reply_markup=builder.as_markup()
    )


# Обработчик выбора темы (callback_data формируется через states.ChooseCallback)
@dp.callback_query(states.ChooseCallback.filter())
async def add_topic_request(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    history = editabs.get_chat_history(user_id, role="assistant")
    if not history:
        await bot.send_message(
            chat_id=user_id,
            text="А тем нет:(",
            reply_markup=buttons.parse_sevendays()
        )
        return

    df = pandas.DataFrame(history)
    df = df[df['title'] != 'НЕ ПО ТЕМЕ']
    counts = df['title'].value_counts()
    count_dict = counts.to_dict()

    callback_data = states.ChooseCallback.unpack(callback.data)
    # Используем переданную страницу или вычисляем её по умолчанию
    page = getattr(callback_data, "page", callback_data.n // 10)

    if user_id not in selected_topics_per_user:
        selected_topics_per_user[user_id] = []
    chosen = selected_topics_per_user[user_id]

    # Переключение выбора темы
    if callback_data.n in chosen:
        chosen.remove(callback_data.n)
    else:
        if len(chosen) >= 5:
            await callback.answer(text="Максимальное количество тем - 5")
            return
        chosen.append(callback_data.n)
    selected_topics_per_user[user_id] = chosen

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size != 0 else 0)
    start_idx = page * page_size
    topics_page = list(count_dict.items())[start_idx:start_idx + page_size]

    builder = InlineKeyboardBuilder()
    row = []
    for global_index, (title, count) in enumerate(topics_page, start=start_idx + 1):

        button_text = "✅" if global_index in chosen else str(global_index)

        data = states.ChooseCallback(
            n=global_index,
            c=len(count_dict),
            ch=",".join(map(str, chosen)),
            page=page
        ).pack()

        row.append(InlineKeyboardButton(text=button_text, callback_data=data))
        if len(row) % 5 == 0:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))

    if chosen:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=states.GenerateCallback(choose=",".join(map(str, chosen))).pack()
        ))

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="Назад",
            callback_data=states.NumberPageCallback(
                page=page - 1,
                choose=",".join(map(str, chosen))
                ).pack()
            ))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=page + 1,
                choose=",".join(map(str, chosen))
                ).pack()
            ))
    if navigation_buttons:
        builder.row(*navigation_buttons)


    await callback.message.edit_text(
            text=callback.message.md_text,
            parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
            reply_markup=builder.as_markup()
        )




@dp.callback_query(states.GenerateCallback.filter())
async def add_topic(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    callback_data = states.GenerateCallback.unpack(callback.data)
    chosen = [int(x) for x in callback_data.choose.split(',') if x]

    history = editabs.get_chat_history(user_id, role="assistant")
    df = pandas.DataFrame(history)
    df = df[df['title'] != 'НЕ ПО ТЕМЕ']
    counts = df['title'].value_counts().to_dict()
    topics = list(counts.keys())

    selected_topics = [topics[i - 1] for i in chosen if 0 <= i - 1 < len(topics)]

    if not selected_topics:
        await callback.answer("Вы не выбрали ни одной темы!", show_alert=True)
        return

        # Вызываем генерацию
    await news.generate_news(callback, selected_topics)

    # После генерации сбрасываем выбранные темы для пользователя
    selected_topics_per_user[user_id] = []




# @dp.callback_query(aiogram.F.data == "generate")
# async def top_titles(callback_query, state: FSMContext):
#     user_id = callback_query.from_user.id
#     chat_id = callback_query.message.chat.id
#     message_id = callback_query.message.message_id
#
#     history  = editabs.get_chat_history(user_id,role="assistant", title=1)
#
#     response = await openai_client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "Выяви из этих заголовков часто повторяющиеся. В ответе предоставь title и url"
#              },
#             {"role": "user", "content": f"Description: {history}\n\n Выяви из этих заголовков часто повторяющиеся и в ответе предоставь топ 5 по убыванию.  В ответе предоставь title и url"}
#             ],
#
#         response_format={
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "titles",
#                 "schema": {
#                     "type": "object",
#                     "properties": {
#                         "topics": {
#                             "type": "array",
#                             "items": {
#                                 "type": "object",
#                                 "properties": {
#                                     "id": {"type": "integer"},
#                                     "title": {"type": "string"},
#                                     "url": {"type": "string"}
#                                     },
#                                 "required": ["id", "title",  "url"],
#                                 "additionalProperties": False
#                                 }
#                             }
#                         },
#                     "required": ["topics"],
#                     "additionalProperties": False
#                     },
#                 "strict": True
#                 }
#             },
#         temperature=0.4
#         )
#
#     response_json = json.loads(response.choices[0].message.content)
#
#     topics_with_descriptions = json.dumps([
#         {
#             "id": topic.get("id"),
#             "title": topic.get("title"),
#             "url": topic.get("url"),
#             "description": editabs.get_description_by_url(topic.get("url", "")) or "Описание не найдено"
#             }
#         for topic in response_json.get("topics", [])
#         ], ensure_ascii=False, indent=4)
#
#
#     json_news = json.loads(topics_with_descriptions)
#
#     news = processing.escape_markdown_v2(json_news)
#
#     await state.update_data(news=json_news, message_id=message_id)
#
#     # await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())
#     await bot.edit_message_text(chat_id=chat_id,
#                                 message_id=message_id, text=news, parse_mode="MarkdownV2", reply_markup=buttons.get_delete_keyboard(json_news), disable_web_page_preview=True)
#

@dp.callback_query(aiogram.F.data == "parse_sevendays")
async def manual_parse(callback_query: types.CallbackQuery):

    chat_id = callback_query.message.chat.id
    await bot.send_message(chat_id=chat_id, text = "Я начал собирать посты с добавленных каналов за 7 дней")

    print(chat_id)
    links = editabs.get_user_url_channel(chat_id)

    for channel_link, in links:

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
                content=f"Ты получишь текст поста, твоя задача выделить основную тему для него, она должна"
                        f"НЕ ИСПОЛЬЗУЙ НИКАКИЕ ЗНАКИ ПРЕПИНАНИЯ"
                        f"содержать в себе конкретные сущности о которых идет речь, выделяй тему не по первым словам, а по всему тексту, "
                        f"придумывай подробную тему.\nЕсть список уже существующих тем: {history}.\n"
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
            editabs.save_chat_history(chat_id, "assistant", topic_id, title, text, url)

            print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")
    await  bot.send_message(chat_id, text="Я закончил")


async def gen_titles_for_titles(channel_link, chat_id):
    await bot.send_message(chat_id, text = "Я начал собирать посты с добавленных каналов за 7 дней")
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
            content=f"Ты получишь текст поста, твоя задача выделить основную тему для него, она должна"
                    f"НЕ ИСПОЛЬЗУЙ НИКАКИЕ ЗНАКИ ПРЕПИНАНИЯ"
                    f"содержать в себе конкретные сущности о которых идет речь, выделяй тему не по первым словам, а по всему тексту, "
                    f"придумывай подробную тему.\nЕсть список уже существующих тем: {history}.\n"
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
        editabs.save_chat_history(chat_id, "assistant", topic_id, title, text, url)

        print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")

