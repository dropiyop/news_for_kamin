import asyncio
import json
from itertools import count

import aiogram.enums
from numpy.ma.core import choose
from pandas.core.interchange.dataframe_protocol import DataFrame
from urllib3 import proxy_from_url
import editabs
from init_client import *
from . import buttons, processing, tg_parse, news, channels
from . import news as package_news
from . import  processing
from aiog import *
import chat
import pandas
import states
import re




@dp.message(aiogram.F.text.lower() == "темы недели")
async def button_channels(message: aiogram.types.Message) -> None:
    user_id = message.from_user.id

    await top_themes(user_id)

    history = editabs.get_top(user_id , gen_id=None)
    chosen_id = ""
    chann = editabs.get_user_channels(user_id)
    if not history or not chann:
        await bot.send_message(chat_id=user_id, text="А тем нет:(",reply_markup=buttons.parse_sevendays())
        await channels.button_channels(message)


    else:
        df = pandas.DataFrame(history)
        counts = df['title'].value_counts()
        counts_dict = counts.to_dict()

        await send_group_list(message, user_id, chosen_id, counts_dict,page=0)

user_chosen_themes = {}
async def send_group_list(message, user_id, chosen_id, count_dict, page=0, chosen=None):
    global user_chosen_themes
    if chosen is None:
        chosen = []  # список выбранных тем



    print(f"send_group_list {chosen_id}")
    print(user_id)
    history = editabs.get_top(user_id, gen_id=None)
    df = pandas.DataFrame(history)
    counts = df['title'].value_counts()
    all_dict = len(counts)

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size else 0)

    start_idx = page * page_size
    end_idx = start_idx + page_size
    topics_page = list(count_dict.items())[start_idx:end_idx]

    # Если выбрана конкретная тема, получаем её подтемы
    if chosen_id:
        chosen_themes = editabs.get_selected_subtopics(user_id, chosen_id)

        # Преобразуем в список заголовков
        if chosen_themes:
            df_themes = pandas.DataFrame(chosen_themes)
            theme_titles = df_themes['title'].to_list()

            # Обновляем словарь для этого пользователя
            user_chosen_themes[user_id] = theme_titles
        else:
            # Если подтем нет, очищаем словарь для этого пользователя
            user_chosen_themes[user_id] = []

    elif chosen_id == '' or not chosen_id:
        user_chosen_themes[user_id] = []

    # Получаем текущий список тем для отображения
    if user_id in user_chosen_themes and user_chosen_themes[user_id]:
        themes = ",\n\n".join(user_chosen_themes[user_id])
    else:
        themes = ""


    text = ("*Вот список обобщенных  тем, о которых говорили за прошлую неделю:*\n"
            "_Выбрав одну из тем - можно увидеть список подтем_\n\n"
            "_Выберите на клавиатуре номера тем_\n\n"
            f"Всего тем: {all_dict}\n\n"
            f"Выбранные Вами  темы: {themes}\n\n")

    builder = InlineKeyboardBuilder()
    row = []

    # Формируем кнопки для каждой темы на текущей странице
    for index, (title, count) in enumerate(topics_page, start=start_idx + 1):
        # Если тема выбрана, можно отметить её галочкой
        button_text = "✅" if index in chosen else str(index)
        text += f"{index}. {title} \n"
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=states.GroupCallback(
                gen_id=index,
                page=page,
                chosen_id = chosen_id
                ).pack()
            ))

        # Разбиваем ряды по 5 кнопок (можно настроить под себя)
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
        builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))

    if chosen_id:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=states.GenerateCallback(chosen_id=chosen_id).pack()
            ))

    text = processing.convert_to_telegram_markdown(text)

    await message.answer(text, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, reply_markup=builder.as_markup())
    await message.delete()

@dp.callback_query(states.GroupCallback.filter())
async def send_sub_topics_page(callback: types.CallbackQuery, callback_data: states.GroupCallback):

    page = callback_data.page
    gen_id = callback_data.gen_id
    print (gen_id)
    user_id = callback.from_user.id

    chosen_id = callback_data.chosen_id
    print (f"send_sub_topics_page {chosen_id}")

    chosen_id_list = chosen_id.split(",")
    chosen_id_list = [int(x) for x in chosen_id_list if x.isdigit()]


    gen_title = editabs.get_top(user_id, gen_id=gen_id)
    title_df = pandas.DataFrame(gen_title)
    gen_title = title_df['title'].to_list()
    print (gen_title)
    gen_title = ",".join(gen_title)


    history = editabs.get_subtop(user_id, gen_id)
    df_subtop = pandas.DataFrame(history)
    counts = df_subtop['title'].value_counts()
    count_dict = counts.to_dict()
    all_dict = len(counts)
    unique_topics = df_subtop['title'].unique()

    history_count_themes = editabs.get_chat_history(user_id, role="assistant", title=1)
    df_chat = pandas.DataFrame(history_count_themes)
    count_history = df_chat['title'].value_counts().to_dict()

    history_counts = {}
    for topic in unique_topics:
        # Получаем количество появлений в истории чата (0, если тема не встречается)
        history_counts[topic] = count_history.get(topic, 0)

    grouped_ids = df_subtop.groupby('title')['subtopic_id'].apply(list).to_dict()

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size != 0 else 0)

    start_idx = page * page_size
    end_idx = start_idx + page_size
    topics_page = list(count_dict.items())[start_idx:start_idx + page_size]
    print(topics_page)


    text = (f"*{gen_title}:*\n"
            "_В скобках указано сколько раз темы повторилась в разных каналах_\n\n"
            "_Выберите на клавиатуре номера тем, по которым нужно сгенерировать новость_\n\n"
            f"Всего тем: {all_dict}\n\n")

    builder = InlineKeyboardBuilder()
    row = []

    # Формируем кнопки для каждой темы на текущей странице
    for local_index, (subtopic_title, count) in enumerate(topics_page):
        display_number = local_index + 1  # Последовательный номер для отображения
        frequency = history_counts.get(subtopic_title, 0)

        # if frequency > 0:

        # Получаем список фактических id для этой темы
        actual_ids = grouped_ids.get(subtopic_title, [])
        # Объединяем их в строку, разделённую запятыми
        actual_id = actual_ids[0] if actual_ids else 0
        # Отображаем галочку, если фактический id уже выбран, иначе показываем порядковый номер
        button_text = f"✅ {display_number}" if actual_id in chosen_id_list  else str(display_number)
        text += f"{display_number}. {subtopic_title} *[{frequency}]*\n"
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=states.ChooseCallback(
                n=actual_id,  # фактический id подтемы
                c=len(count_dict),
                chosen_id=chosen_id,  # все фактические id для этой подтемы
                page=page,
                gen_id=gen_id
                ).pack()
            ))
        if len(row) == 5:
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
                chosen_id=chosen_id,
                gen_id=gen_id
            ).pack()
        ))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=page + 1,
                chosen_id=chosen_id,
                gen_id = gen_id
            ).pack()
        ))
    if navigation_buttons:
        builder.row(*navigation_buttons)

    if chosen_id:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=states.GenerateCallback(chosen_id=chosen_id).pack()
            ))

     # Добавляем кнопку для возврата к глобальным темам
    builder.row(InlineKeyboardButton(
        text="Назад к глобальным темам",
        callback_data=states.BackCallback(chosen_id=chosen_id).pack()
        ))
    # builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))

    text = processing.convert_to_telegram_markdown(text)

    await callback.message.edit_text(text = text, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, reply_markup=builder.as_markup())





@dp.callback_query(states.NumberPageCallback.filter())
async def navigate_page(callback: types.CallbackQuery, callback_data: states.NumberPageCallback):
    new_page = callback_data.page

    # Преобразуем строку с выбранными темами в список целых чисел
    chosen_id = callback_data.chosen_id

    gen_id  = callback_data.gen_id

    page = callback_data.page

    chosen_id_list = chosen_id.split(",")
    chosen_id_list = [int(x) for x in chosen_id_list if x.isdigit()]

    user_id = callback.from_user.id

    gen_title = editabs.get_top(user_id, gen_id=gen_id)
    title_df = pandas.DataFrame(gen_title)
    gen_title = title_df['title'].to_list()
    print(gen_title)
    gen_title = ",".join(gen_title)

    history = editabs.get_subtop(user_id, gen_id)
    df = pandas.DataFrame(history)
    counts = df['title'].value_counts()
    count_dict = counts.to_dict()
    all_dict = len(counts)

    grouped_ids = df.groupby('title')['subtopic_id'].apply(list).to_dict()

    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size != 0 else 0)
    start_idx = page * page_size
    topics_page = list(count_dict.items())[start_idx:start_idx + page_size]

    text = (
        f"*{gen_title}:*\n"
         "_В скобках указано сколько раз темы повторилась в разных каналах_\n\n"
        "_Выберите на клавиатуре номера тем, по которым нужно сгенерировать новость_\n\n"
        f"Всего тем: {all_dict}\n\n")


    builder = InlineKeyboardBuilder()
    row = []

    for local_index, (subtopic_title, count) in enumerate(topics_page):
        display_number = local_index + 1
        actual_ids = grouped_ids.get(subtopic_title, [])
        actual_id = actual_ids[0] if actual_ids else 0
        # Отображаем галочку, если выбран фактический id
        button_text = f"✅ {display_number}" if actual_id in chosen_id_list else str(display_number)
        text += f"{display_number}. {subtopic_title} *[{count}]*\n"
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=states.ChooseCallback(
                n=actual_id,
                c=len(count_dict),
                chosen_id=",".join(map(str, chosen_id_list)),
                page=page,
                gen_id=gen_id
                ).pack()
            ))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    updated_chosen_str = ",".join(map(str, chosen_id_list))

    # builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))


    if updated_chosen_str:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=updated_chosen_str
        ))

    navigation_buttons = []
    if new_page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="Назад",
            callback_data=states.NumberPageCallback(
                page=new_page - 1,
                chosen_id=updated_chosen_str,
                gen_id = gen_id
            ).pack()
        ))
    if new_page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=new_page + 1,
                chosen_id=updated_chosen_str,
                gen_id=gen_id

            ).pack()
        ))
    if navigation_buttons:
        builder.row(*navigation_buttons)

        # Добавляем кнопку для возврата к глобальным темам
    builder.row(InlineKeyboardButton(
        text="Назад к глобальным темам",
        callback_data=states.BackCallback(chosen_id=chosen_id).pack()
        ))

    await callback.message.edit_text(
        text=text,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN,
        reply_markup=builder.as_markup()
    )



# Обработчик выбора темы (callback_data формируется через states.ChooseCallback)
@dp.callback_query(states.ChooseCallback.filter())
async def add_topic_request(callback: types.CallbackQuery,  callback_data: states.ChooseCallback):

    chosen_id_str = callback_data.chosen_id
    chosen_id_list = [int(x) for x in chosen_id_str.split(",") if x.strip().isdigit()]
    print( f"add_topic_request {chosen_id_list}")

    gen_id = callback_data.gen_id
    page = callback_data.page
    user_id = callback.from_user.id

    history = editabs.get_subtop(user_id,gen_id)


    if not history:
        await bot.send_message(
            chat_id=user_id,
            text="А тем нет:(",
            reply_markup=buttons.parse_sevendays()
        )

    df = pandas.DataFrame(history)
    counts = df['title'].value_counts()
    count_dict = counts.to_dict()
    grouped_ids = df.groupby('title')['subtopic_id'].apply(list).to_dict()

    # Определяем выбранный фактический id из нажатой кнопки
    chosen_subtopic_id = callback_data.n
    print("Нажатый фактический id:", chosen_subtopic_id)

    # Переключаем выбор: если уже выбран, удаляем; иначе добавляем (лимит 5)
    if chosen_subtopic_id in chosen_id_list:
        chosen_id_list.remove(chosen_subtopic_id)
    else:
        if len(chosen_id_list) >= 5:
            await callback.answer("Максимальное количество тем - 5", show_alert=True)
            return
        chosen_id_list.append(chosen_subtopic_id)
    # Обновляем строковое представление выбранных id
    print("Обновлённый список выбранных id:", chosen_id_list)


    page_size = 10
    total_pages = (len(count_dict) // page_size) + (1 if len(count_dict) % page_size != 0 else 0)
    start_idx = page * page_size
    topics_page = list(count_dict.items())[start_idx:start_idx + page_size]

    text = (
        f"*{', '.join(title for title in df['title'].unique())}:*\n"
        "_В скобках указано, сколько раз тема повторилась_\n\n"
        "_Выберите номер подтемы для генерации новости_\n\n"
        f"Всего подтем: {len(count_dict)}\n\n"
    )

    builder = InlineKeyboardBuilder()
    row = []

    for local_index, (subtopic_title, count) in enumerate(topics_page):
        display_number = local_index + 1
        actual_ids = grouped_ids.get(subtopic_title, [])
        actual_id = actual_ids[0] if actual_ids else 0
        # Отображаем галочку, если выбран фактический id
        button_text = f"✅ {display_number}" if actual_id in chosen_id_list else str(display_number)
        text += f"{display_number}. {subtopic_title} *[{count}]*\n"
        row.append(InlineKeyboardButton(
            text=button_text,
            callback_data=states.ChooseCallback(
                n=actual_id,
                c=len(count_dict),
                chosen_id=",".join(map(str, chosen_id_list)),
                page=page,
                gen_id=gen_id
                ).pack()
            ))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    updated_chosen_str = ",".join(map(str, chosen_id_list))

    print(chosen_id_list)
    # builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_choose"))
    # Добавляем кнопку для возврата к глобальным темам


    if updated_chosen_str:
        builder.row(InlineKeyboardButton(
            text="Сгенерировать новость",
            callback_data=states.GenerateCallback(chosen_id=updated_chosen_str).pack()
        ))

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(
            text="Назад",
            callback_data=states.NumberPageCallback(
                page=page - 1,
                chosen_id=",".join(map(str, chosen_id_list)),
                gen_id = gen_id
                ).pack()
            ))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(
            text="Вперёд",
            callback_data=states.NumberPageCallback(
                page=page + 1,
                chosen_id=",".join(map(str, chosen_id_list)),
                gen_id = gen_id
                ).pack()
            ))
    if navigation_buttons:
        builder.row(*navigation_buttons)

    builder.row(InlineKeyboardButton(
        text="Назад к глобальным темам",
        callback_data=states.BackCallback(chosen_id=updated_chosen_str).pack()
        ))


    await callback.message.edit_text(
            text=callback.message.md_text,
            parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
            reply_markup=builder.as_markup()
        )

@dp.callback_query(states.BackCallback.filter())
async def back_to_groups(callback: types.CallbackQuery, callback_data: states.BackCallback):
    user_id = callback.from_user.id
    chosen_id = callback_data.chosen_id

    print(f"back_to_groups {chosen_id}")
    # Получаем глобальные темы для пользователя
    history = editabs.get_top(user_id)
    if not history:
        await bot.send_message(chat_id=user_id, text="Глобальных тем нет или что-то сломалось")
        return
    df = pandas.DataFrame(history)
    counts = df['title'].value_counts()
    count_dict = counts.to_dict()
    page = 0

    await send_group_list(callback.message,user_id,chosen_id, count_dict, page=page)


@dp.callback_query(aiogram.F.data == "cancel_choose")
async def cancel_channel_request(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=callback.message.md_text,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        reply_markup=None)



@dp.callback_query(states.GenerateCallback.filter())
async def add_topic(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    callback_data = states.GenerateCallback.unpack(callback.data)
    chosen = callback_data.chosen_id
    print (chosen)
    history = editabs.get_selected_subtopics(user_id, chosen)
    df = pandas.DataFrame(history)
    counts = df['title'].to_list()
    # counts = ",".join(counts)
    print (counts)



    selected_topics = counts
    if not selected_topics:
        await callback.answer("Вы не выбрали ни одной темы!", show_alert=True)
        return

        # Вызываем генерацию
    await news.generate_news(callback, selected_topics)



async def top_themes(user_id):
    """
    Отправляет запрос в GPT для генерации 10 общих тем с вложенными подтемами.
    Возвращает JSON со структурой {id: {общая_тема, подтемы}}.
    """

    history = editabs.get_chat_history(user_id, "assistant", title = 1)
    gen_titles = editabs.get_top(user_id)

    df  = pandas.DataFrame(history)
    df = df[df['title'] != 'НЕ ПО ТЕМЕ']
    counts_dict = df.to_dict()

    print (counts_dict)


    prompt = (
        f"Сделай список из 10 глобальных IT-тем и подтем ТОЛЬКО на основе этих тем из словаря {counts_dict}\n"
        f"Если темы одинаковые, то выбери только одну"
        f"НЕ СОРТИРУЙ так, чтобы одна и та же тема была в  2 разных глобальных категориях"
        f"НЕ ПРИДУМЫВАЙ ПОДТЕМЫ, используй только те, что есть. НЕЛЬЗЯ ПРИДУМЫВАТЬ ДРУГИЕ ПОДТЕМЫ"
        f"У тебя есть только словарь с темами, не вздумай придумывать свои подтемы"
        f"Если ты добавишь свою подтему, у меня сломается база данных, пожалуйста, сортируй только предоставленные темы!"
        f"Группируй темы чтобы они как можно лучше соответствовали друг другу!"
        f"В каждой глобальной теме должно быть минимум 5 подтем. Должны быть рассортированы все темы, даже если ты получил 100 тем"
        f"То ты должен их все рассортировать"
        f"Если уже есть основная тема и она подходит, то ни в коем случае не создавай новую - пользуйся той, что уже есть"
        f"Если подтему можно добавить в уже существующую тему - сделай это"
        "- Название общей темы НИКОГДА НЕ ДОЛЖНО ПОВТОРЯТЬСЯ (`title`).\n"
        f"- Дай список подтем (`subtopics`)\n"
        f"То есть ты сначала формируешь глобальные темы на основе всего словаря который я тебе присылаю, а затем добавляешь подтемы на основе того же словаря"
        f"В уже созданные тобой глобальные темы"
        # "- Имеет `id`, связанный с общей темой (например, если `id` общей темы = 1, то её подтемы могут быть 101, 102, 103).\n"
        # "- Имеет название `title`.\n\n"
        "Ответ верни **в формате JSON** с ключами `topics`, вложенность должна быть строгой.\n"
        "Пример JSON:\n"
        "{\n"
        '  "topics": [\n'
        '    { "id": 1, "title": "Искусственный интеллект", "subtopics": [\n'
        '      { "id": 101, "title": "Обработка естественного языка" },\n'
        '      { "id": 102, "title": "Компьютерное зрение" }\n'
        "    ] },\n"
        "    { \"id\": 2, \"title\": \"Кибербезопасность\", \"subtopics\": [\n"
        "      { \"id\": 201, \"title\": \"Шифрование данных\" },\n"
        "      { \"id\": 202, \"title\": \"Атаки на нейросети\" }\n"
        "    ] }\n"
        "  ]\n"
        "}"
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты создаёшь структурированные IT-темы для базы данных."},
            {"role": "user", "content": prompt}
            ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "topic_hierarchy",
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
                                    "subtopics": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "title": {"type": "string"}
                                                },
                                            "required": ["id", "title"],
                                            "additionalProperties": False
                                            }
                                        }
                                    },
                                "required": ["id", "title", "subtopics"]
                                }
                            }
                        },
                    "strict": True
                    }
                }
            },
        temperature=0.2
        )


    response_json = json.loads(response.choices[0].message.content)

    print (response_json)

    editabs.save_top_subtop(response_json, user_id)

    return response_json



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
                # msg.message = await processing.compress_text(msg.message)
                if msg.message not in seen_messages:
                    seen_messages.add(msg.message)
                    selected_description.append({
                        "message": msg.message,
                        "link": link
                        })


        for description in selected_description:
            print(description)
            history = editabs.get_chat_history(chat_id, role ="assistant", title=1)
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
                        f"формулируй подробную тему. Если в новости упоминается конкретный продукт, группируй их в одну тему. \n" \
                        f"Примеры хороших тем: 'Улучшения в нейросетевых моделях на примере GPT-4.5', 'Тренды и навыки в ML-инженерии на 2025 год', \n" \
                        f"'Интеграция ChatGPT в образовательные учреждениях для учеников старших классов'. \n" \
                        f"Игнорируй посты с хэштегом #Реклама"
                        f"К рекламе также относятся заголовки на подобии:"
                        f"Вебинар AI-агенты на практике: глубоко и по существу"
                        f"Введение в AI-агентов и их применение в бизнесе на примере вебинара от Сбера"
                        f"Вакансии в области NLP и CV в Европе и России с акцентом на удаленную работу "
                        f"Инструменты искусственного интеллекта для поддержания здоровья и благополучия на примере 'здесь программа'"
                        f"Использование Gen-AI в музыкальной платформе Soundverse для создания музыки начинающими музыкантами"
                        f"Инструмент Zebracat для создания маркетинговых видео с использованием искусственного интеллекта"
                        f"Тренировки по ML от яндекса с акцентом на компьютерное зрение и генеративные модели"
                        f"НЕ ИСПОЛЬЗУЙ ПОДОБНЫЕ ЗАГОЛОВКИ"
                        f"НЕ анализируй тексты короче 50 символов, \n" \
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



            editabs.save_chat_history(chat_id, "assistant", topic_id, title, text, url)
            print(chat_id)

            print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")

    await top_themes(chat_id)
    await  bot.send_message(chat_id, text="Я закончил")


async def gen_titles_for_titles(channel_link, chat_id):
    await bot.send_message(chat_id, text = f"Я начал собирать посты с {channel_link} за 7 дней", disable_web_page_preview=True)
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
            # msg.message = await processing.compress_text(msg.message)
            if msg.message not in seen_messages:
                seen_messages.add(msg.message)
                selected_description.append({
                    "message": msg.message,
                    "link": link
                    })

        for description in selected_description:

            history = editabs.get_chat_history(chat_id, role ="assistant", title=1)
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
                        f"формулируй подробную тему. Если в новости упоминается конкретный продукт, группируй их в одну тему. \n" \
                        f"Примеры хороших тем: 'Улучшения в нейросетевых моделях на примере GPT-4.5', 'Тренды и навыки в ML-инженерии на 2025 год', \n" \
                        f"'Интеграция ChatGPT в образовательные учреждениях для учеников старших классов'. \n" \
                        f"Игнорируй посты с хэштегом #Реклама"
                        f"К рекламе также относятся заголовки на подобии:"
                        f"Вебинар AI-агенты на практике: глубоко и по существу"
                        f"Введение в AI-агентов и их применение в бизнесе на примере вебинара от Сбера"
                        f"Вакансии в области NLP и CV в Европе и России с акцентом на удаленную работу "
                        f"Инструменты искусственного интеллекта для поддержания здоровья и благополучия на примере 'здесь программа'"
                        f"Использование Gen-AI в музыкальной платформе Soundverse для создания музыки начинающими музыкантами"
                        f"Инструмент Zebracat для создания маркетинговых видео с использованием искусственного интеллекта"
                        f"Тренировки по ML от яндекса с акцентом на компьютерное зрение и генеративные модели"
                        f"НЕ ИСПОЛЬЗУЙ ПОДОБНЫЕ ЗАГОЛОВКИ"
                        f"НЕ анализируй тексты короче 50 символов, \n" \
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
                temperature=0.2
                )

            response_json = json.loads(response.choices[0].message.content)


            topic_id = 1
            title = response_json.get("title").strip()
            text = description['message']
            url = description['link']
            editabs.save_chat_history(chat_id, "assistant", topic_id, title, text, url)
            print (chat_id)

            print(f"Обработан ссылка: {description['link']} и отправлен в GPT.")

    # await top_themes(chat_id)
    await  bot.send_message(chat_id, text="Я закончил")
