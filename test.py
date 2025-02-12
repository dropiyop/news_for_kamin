import openai

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import re
import json
import requests
from aiogram.fsm.context import FSMContext
from aiogram import F
import base64
from aiogram import types
import os
import dotenv
import httpx
import httpx_socks
import editabs

dotenv.load_dotenv()

flag = False
# Объявление глобальных переменных
generate_text = None,
image_url = None


init_clients = set()  # Инициализация списка для хранения данных пользователей
used_titles = set()  # Инициализация списка для хранения использованных заголовков
user_prompts = {}


def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2 и форматирует список тем"""
    escape_chars = r"_*[]()~`>#+-=|{}.!"

    # Если передан список кортежей (id, title, url), форматируем в MarkdownV2
    if isinstance(text, list):
        formatted_text = []
        for topic in text:
            topic_id = str(topic.get("id", ""))
            title = topic.get("title", "")
            url = topic.get("url", "")
            if url:
                formatted_text.append(f" {topic_id}.\n {title}\n({url})\n")
            else:
                formatted_text.append(f" {topic_id}.\n {title}\n")

        text = "".join(formatted_text)

    # Экранируем специальные символы для MarkdownV2
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)






transport = httpx_socks.AsyncProxyTransport.from_url(f"socks5://{os.getenv('PROXY_URL')}:{os.getenv('PROXY_PORT')}")
http_client = httpx.AsyncClient(transport=transport)

openai_client =  openai.AsyncOpenAI(api_key=os.getenv('OPENAI_TOKEN'), http_client=http_client)





async def shutdown_handler(bot):

    await bot.session.close()


# Конфигурация
CASCADE_USER = os.getenv('CASCADE_USER')
CASCADE_PASSWORD = os.getenv('CASCADE_PASSWORD')
CASCADE_USERS_URL = os.getenv('CASCADE_USERS_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')



bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
request_count = 0
cached_data = None


@dp.message(Command("start"))
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if any([user_id == user[0] for user in init_clients]):
        return
    kb = [[types.KeyboardButton(text="Отправить свой профиль", request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Нажмите кнопку ниже"
        )
    text = (f"Здравствуй, {(message.from_user.full_name)}!\nДля работы в этом боте вы должны быть "
            f"сотрудником ГК КАМИН. Для этого отправьте данные своего профиля кнопкой снизу. "
            f"Я смогу подтвердить, что вы сотрудник по номеру телефона"),
    await message.answer(text=text[0], reply_markup=keyboard)
    await state.set_state(states.Form.waiting_for_contact)


def clean_phone_number(phone_number):
    cleaned_number = re.sub(r'\D', '', phone_number)
    return cleaned_number



@dp.message(states.Form.waiting_for_contact, F.content_type == "contact")
async def contact_handler(message: types.Message, state: FSMContext) -> None:
    contact = message.contact
    await state.clear()
    contact_id = contact.user_id
    contact_name = contact.first_name
    contact_phone = contact.phone_number
    contact_username = message.from_user.username
    chat_id = None

    if contact_id == message.from_user.id:
        if not any([contact_id == user[0] for user in init_clients]):
            url = CASCADE_USERS_URL
            credentials = f'{CASCADE_USER}:{CASCADE_PASSWORD}'
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            headers = {'Authorization': f'Basic {encoded_credentials}'}

            response = requests.get(url, headers=headers)
            print(response)

            if response.status_code == 200:
                data = response.json()
                for record in data:
                    if clean_phone_number(contact_phone)[1:] == clean_phone_number(record['mobilePhone'])[1:]:
                        contact_name = record['shortName']
                        editabs.add_init_client(contact_id, chat_id, contact_username, contact_name, contact_phone)
                        fio = record['name'].split(" ")
                        await message.answer(f"{fio[1]} {fio[2]}, Поздравляю! "
                                             f"Вы можете использовать функциональность бота",
                                             reply_markup=types.ReplyKeyboardRemove())

                        await send_welcome(message)

                        break
                else:

                    await message.answer("К сожалению, вы не были найдены в базе данных сотрудников Каскада. "
                                         "Вы не сможете использовать бота.", reply_markup=types.ReplyKeyboardRemove())
            else:

                await message.answer("Возникли проблемы при подключении к базе данных Каскада. Попробуйте позже.")
    else:
        await message.answer("Ну так не честно, это же не ваш контакт")




def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Придумать новость", callback_data="generate")],
        [InlineKeyboardButton(text="Свой запрос вкл\выкл", callback_data="toggle_prompt")],
        [InlineKeyboardButton(text="Изменить каналы", callback_data="change")]
        ])

    return keyboard


def get_inline_keyboard2():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Придумать новость", callback_data="generate")],
        # [InlineKeyboardButton(text="Опубликовать", callback_data="publish")],
        [InlineKeyboardButton(text="Свой запрос вкл\выкл", callback_data="toggle_prompt")],
        [InlineKeyboardButton(text="Новая Картинка на основе статьи", callback_data="new_image")],
        [InlineKeyboardButton(text="Изменить каналы", callback_data="change")]

        ])
    return keyboard


def get_inline_keyboard3():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Придумать новость", callback_data="generate")],
        [InlineKeyboardButton(text="Свой запрос вкл\выкл", callback_data="toggle_prompt")],
        [InlineKeyboardButton(text="Новая Картинка на основе статьи", callback_data="new_image")],
        [InlineKeyboardButton(text="Изменить каналы", callback_data="change")]
        ])
    return keyboard

def get_inline_keyboard4():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")],
    [InlineKeyboardButton(text="Список каналов", callback_data="list_channels")],
    [InlineKeyboardButton(text="Удалить ВСЕ каналы", callback_data="remove_all_channels")],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_inline_keyboard5():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Придумать новость", callback_data="gen_news")],
        [InlineKeyboardButton(text="Свой запрос вкл\выкл", callback_data="toggle_prompt")],
        [InlineKeyboardButton(text="Новая Картинка на основе статьи", callback_data="new_image")],
        [InlineKeyboardButton(text="Изменить каналы", callback_data="change")]
        ])
    return keyboard



def back_or_titles():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")],
        [InlineKeyboardButton(text="Надо бы каналы спарсить", callback_data="generate_titles")]
        ])

    return keyboard

def back():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]

        ])

    return keyboard

def get_delete_keyboard(news):

    keyboard = InlineKeyboardBuilder()

    for i in range(len(news)):


        keyboard.button(text=f"Удалить {i + 1}", callback_data=f"delete_topic_{i}")

    keyboard.button(text="Закончить", callback_data="confirm_topics")

    keyboard.adjust(2)

    return keyboard.as_markup()

@dp.callback_query(lambda c: c.data.startswith("delete_topic_"))
async def delete_selected_topic(callback_query: types.CallbackQuery, state: FSMContext):
    """Удаляет выбранную тему и обновляет сообщение"""
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
    formatted_news = escape_markdown_v2(news)

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=message_id,
        text=f"{formatted_news}",
        parse_mode="MarkdownV2",
        reply_markup=get_delete_keyboard(news),
        disable_web_page_preview=True
    )

    await state.update_data(formatted_news=formatted_news)


@dp.callback_query(lambda c: c.data == "confirm_topics")
async def confirm_topics(callback_query: types.CallbackQuery, state: FSMContext):
    """Окончательное подтверждение тем"""
    user_data = await state.get_data()
    news = user_data.get("news", [])

    formatted_news = escape_markdown_v2(news)

    await callback_query.message.edit_text(
        f"Итоговый список тем:\n\n{formatted_news}",
        parse_mode="MarkdownV2", reply_markup=get_inline_keyboard5(),
        disable_web_page_preview=True
    )

    await state.update_data(pending_function=generate_news, formatted_news=formatted_news)


    # await state.clear()  #  Очищаем state после завершения







@dp.callback_query(lambda c: c.data == "generate_titles")
async def generate_titles(callback: types.CallbackQuery):

    await callback.message.edit_text("Я сделаю это и напишу как закончу",parse_mode="Markdown", reply_markup=get_inline_keyboard3())
    await gen_titles(callback)  #




@dp.callback_query(lambda c: c.data == "add_channel")
async def add_channel_request(callback: types.CallbackQuery):
    """Сообщение о добавлении канала"""
    await callback.message.edit_text("Можно много или одну ссылку в формате:\n`https://t.me/channel_name`", parse_mode="Markdown",reply_markup=back())



@dp.message(lambda message: message.text.startswith("https://t.me/"))
async def add_channel(message: types.Message):

    user_id = message.from_user.id
    raw_text = message.text.strip()

    # Разделяем текст по пробелу, запятой или новой строке
    channels = {ch.strip() for ch in raw_text.replace(",", " ").split()}

    # Фильтруем только корректные ссылки
    valid_channels = {ch for ch in channels if ch.startswith("https://t.me/")}

    if not valid_channels:
        await message.reply("Не найдено корректных ссылок! Проверьте формат.")
        return



    # Определяем уже существующие и новые каналы
    new_channels = valid_channels - set(editabs.get_user_channels(user_id))
    existing_channels = valid_channels & set(editabs.get_user_channels(user_id))

    # Добавляем новые каналы в базу данных
    for channel in new_channels:
        editabs.add_user_channel(user_id, channel)

    # Формируем ответ
    response = "Добавлены каналы:\n" + "\n".join(f" {ch}" for ch in new_channels) if new_channels else ""


    if existing_channels:
        response += "\n!!! Эти каналы уже были в списке:\n" + "\n".join(f" {ch}" for ch in existing_channels)

    await message.reply(response or " Нет новых каналов для добавления.", reply_markup=back_or_titles(), disable_web_page_preview=True)





def escape_markdown(text: str) -> str:
    """Экранирует специальные символы MarkdownV2"""
    escape_chars = r"_*[]()~`>#+-=|{}.!<>"
    return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", text)


@dp.callback_query(lambda c: c.data == "list_channels")
async def list_channels(callback: types.CallbackQuery):
    user_id = callback.from_user.id  # Получаем user_id
    channels = editabs.get_user_channels(user_id)

    if not channels:
        await callback.message.edit_text("Список каналов пуст.", reply_markup=back())
        return

    keyboard = InlineKeyboardBuilder()

    for i, channel in enumerate(channels, start=1):
        keyboard.button(text=f"Удалить {i}", callback_data=f"remove_channel:{channel}")

    keyboard.button(text="Назад", callback_data="back")
    keyboard.adjust(1)  # Каждая кнопка в отдельной строке

    channels_text = "\n".join(f"{i} {escape_markdown(channel)}" for i, channel in enumerate(channels, start=1))
    await callback.message.edit_text(f"*Список каналов:*\n\n{channels_text}",
                                     parse_mode="MarkdownV2",
                                     reply_markup=keyboard.as_markup(),
                                     disable_web_page_preview=True)



@dp.callback_query(lambda c: c.data.startswith("remove_channel:"))
async def remove_channel(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    channels = editabs.get_user_channels(user_id)

    channel = callback.data.replace("remove_channel:", "")

    if channel not in channels:
        await callback.answer("Канал уже удалён!", show_alert=True)
        return

    editabs.remove_user_channel(user_id,channel)


    await callback.answer(f"Канал {channel} удален!")

    # Обновляем список каналов
    await list_channels(callback)

def yesorno():
    keyboard = (InlineKeyboardMarkup
    (inline_keyboard=[
    [InlineKeyboardButton(text="ДА", callback_data="yes")],
    [InlineKeyboardButton(text="нет", callback_data="no")]
    ])
    )

    return keyboard




@dp.callback_query(lambda c: c.data == "remove_all_channels")
async def confirm_remove_all_channels(callback: types.CallbackQuery):

    await callback.message.edit_text("ТЫ УВЕРЕН?", parse_mode="Markdown",reply_markup=yesorno())



@dp.callback_query(lambda c: c.data == "yes")
async def remove_all_channels(callback: types.CallbackQuery):
    """Удаление всех каналов после подтверждения"""
    user_id = callback.from_user.id

    channels = editabs.get_user_channels(user_id)

    if not channels:
        await callback.answer("Список каналов пуст", show_alert=True)
        return

    # Удаляем все каналы пользователя из базы данных
    editabs.all_remove_channels(user_id)

    await callback.message.edit_text(" Все каналы успешно удалены!", parse_mode="Markdown", reply_markup=get_inline_keyboard4())

@dp.callback_query(lambda c: c.data == "no")
async def remove_all_channels(callback: types.CallbackQuery):

    await callback.message.edit_text("ты не уверен", parse_mode="Markdown", reply_markup=get_inline_keyboard4())


@dp.callback_query(lambda c: c.data == "back")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Сделай это снова", parse_mode="Markdown",reply_markup=get_inline_keyboard4())




@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Давай, придумывай", parse_mode="Markdown",reply_markup=get_inline_keyboard())




@dp.callback_query(lambda c: c.data == "change")
async def edit_channels_menu(callback: types.CallbackQuery):


    await callback.message.edit_text("Действуй:", reply_markup= get_inline_keyboard4())


@dp.callback_query(lambda c: c.data == "toggle_prompt")
async def toggle_prompt_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id



    # Проверяем, включен ли пользовательский промпт для данного пользователя
    if user_id in user_prompts:
        del user_prompts[user_id]  # Удаляем пользовательский промпт
        await callback_query.message.answer("Пользовательский промпт отключен. Теперь новости будут придумываться сами", reply_markup=get_inline_keyboard3())
    else:
        # Если пользовательский промпт выключен, запрашиваем его ввод
        await callback_query.message.answer("Пожалуйста, введите свой запрос:")
        await state.set_state(states.Form.waiting_for_prompt)

    await callback_query.answer()


@dp.message(states.Form.waiting_for_prompt)
async def prompt_handler(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_prompt = message.text  # Получаем пользовательский промпт



    # Сохраняем пользовательский промпт в словаре
    user_prompts[user_id] = user_prompt

    await message.answer("Ваш промпт сохранен. Теперь можно нажать 'Придумать новость' для создания статьи по вашему промпту.", reply_markup=get_inline_keyboard3())
    # Возвращаемся в начальное состояние
    await state.clear()  # Очищаем состояние

def slice_text(text, num_words):
    """Берет первые num_words слов из текста, чтобы создать заголовок"""
    words = text.split()[:num_words]  # Берем первые `num_words` слов
    return " ".join(words)  # Соединяем их обратно в строку



async def compress_text(text):
    max_length = 1000
    return text[:max_length] if len(text) > max_length else text





#######################################################################################################







async def send_telegram_message(chat_id, text, reply_markup=None, bot=None):
    # Используем асинхронный метод для отправки сообщения в Telegram
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)



async def send_long_message(chat_id, text, bot, reply_markup=None):
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4096], reply_markup=reply_markup if i + 4096 >= len(text) else None, parse_mode="Markdown")


async def send_welcome(message: types.Message):
    await message.reply("Готов для генерации новостей!", reply_markup=get_inline_keyboard())

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
                await bot.send_message(chat_id, messages, reply_markup=get_inline_keyboard4())  # Отправляем пользователю сообщение об ошибке
                return
            else:
                seen_messages = set()
                selected_description = []

                for msg in messages:
                    if not msg.message.strip():
                        continue

                    link = f"{channel}/{msg.id}"
                    msg.message = await compress_text(msg.message)
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
            await bot.send_message(chat_id, f"Ошибка при парсинге", reply_markup=get_inline_keyboard3())

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

    await bot.send_message(chat_id, "С парсингом я закончил", reply_markup=get_inline_keyboard3())




async def top_titles(callback_query):

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

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



    return topics_with_descriptions

async def generate_news(callback_query, state: FSMContext):
    global generate_text, user_prompts

    message_id = callback_query.message.message_id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    user_data = await state.get_data()

    topics_with_descriptions = user_data

    print (topics_with_descriptions)

    await  state.clear()


    # Проверяем, существует ли пользовательский промп
    if user_id in user_prompts:
        # Используем промпт, заданный пользователем
        prompt = (user_prompts[user_id] + "\nОсновные правила для тебя:"

                                          "\nТы IT-блогер c многомиллионной аудиторией. Самый лучший. Тебе нельзя ошибаться. Твои подписчики ждут от тебя только самых интересных новостей"
                                          "1.Всего в статье должно быть 1500 символов. НИКОГДА НЕ МОЖЕТ БЫТЬ БОЛЬШЕ 1500 СИМВОЛОВ.  2.Структура статьи должна обязательно иметь заголовок, основную часть, заключение."
                                          "3.Структурные наименования писать не нужно не нужно."
                                          "4.Статья должна иметь завершенный вид и быть интересной"
                                          "Тебе придут новости из новостных каналов за неделю. Выяви самые интеренсые новости об IT-индстурии, сфокусируйся на новостях об искусственном интеллекте"
                                          "Напиши одну IT-статью (Всего в статье должно быть 1500 символов, ИНАЧЕ Я ТЕБЯ УВОЛЮ) на основе заголовков и описаний, которые придут тебе из RSS ленты. Ограничение на количество символов статьи = 1500"
                                          "При каждой генерации используй разные статьи. Если нужно будет сгенерировать повторно, тебе нужно придумать новую статью, основываясь на других заголовках. "
                                          "Всегда рандомно выбирай статьи. Суммаризируй весь текст ровно до 1500 символов.  Не включай ссылки в свои статьи\n\n"
                  )
    else:





        await bot.send_message(chat_id=chat_id, text="Генерация новости: 20%")

        prompt = (
            "\nОсновные правила для тебя:"

            "\nТы IT-блогер c многомиллионной аудиторией. Самый лучший. Тебе нельзя ошибаться. Твои подписчики ждут от тебя только самых интересных новостей"
            "1.Всего в статье должно быть 1500 символов. НИКОГДА НЕ МОЖЕТ БЫТЬ БОЛЬШЕ 1500 СИМВОЛОВ.  2.Структура статьи должна обязательно иметь заголовок, основную часть, заключение."
            "3.Структурные наименования писать не нужно не нужно."
            "4.Статья должна иметь завершенный вид и быть интересной"
            "Тебе придет json {'id': 'title': 'url': 'description':}"
            "новости из новостных каналов за неделю. Выяви самые интеренсые новости об IT-индстурии, сфокусируйся на новостях об искусственном интеллекте"
            "Напиши одну IT-статью (Всего в статье должно быть 1500 символов, ИНАЧЕ Я ТЕБЯ УВОЛЮ) на основе заголовков и описаний, которые придут тебе из RSS ленты. Ограничение на количество символов статьи = 1500"
            "При каждой генерации используй разные статьи. Если нужно будет сгенерировать повторно, тебе нужно придумать новую статью, основываясь на других заголовках. "
            "Всегда рандомно выбирай статьи. Суммаризируй весь текст ровно до 1500 символов.  Не включай ссылки в свои статьи\n\n"

        )
        prompt += f"Description: {topics_with_descriptions}\n\n"

        print(topics_with_descriptions)

    await bot.send_message(chat_id=chat_id, text="Генерация новости: 50%")

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "У тебя есть группа в социальной сети и ты должен придумывать по одной статье на основе предложенных  description. Ограничение на количество символов в статье строго 1500"},
            {"role": "user", "content": prompt}
            ],

        temperature=0.7,
        )

    # Получение текста из ответа
    generate_text = response.choices[0].message.content.strip()



    # print(prompt)
    await bot.send_message(chat_id=chat_id, text="Генерация новости: 70%")

    #     # Генерация изображения на основе текста статьи
    #     image_prompt = f"Create an illustration for the following article: {generate_text}"
    #     image_response = await openai_client.images.generate(
    #         model="dall-e-3",
    #         prompt=image_prompt,
    #         size="1024x1024",
    #         quality="standard",
    #         n=1
    #         )
    #
    #     image_url = image_response.data[0].url
    #     await bot.send_message(chat_id=chat_id, text="Генерация новости: 100%")
    #
    #     return generate_text, image_url
    #
    #
    # @dp.callback_query(lambda c: c.data == "new_image")
    # async def new_image_handler(callback_query: types.CallbackQuery):
    #     global generate_text, image_url
    #
    #     chat_id = callback_query.message.chat.id
    #
    #     # Проверяем, определен ли текст статьи
    #     if not generate_text:
    #         await callback_query.message.reply("Ошибка: текст статьи не найден. Пожалуйста, сгенерируйте новость сначала.")
    #         return
    #
    #     await bot.send_message(chat_id=chat_id, text="Генерация новой картинки: 20%")
    #
    #     # Генерация изображения на основе уже сгенерированного текста статьи
    #     image_prompt = f"Create an illustration for the following article: {generate_text}"
    #     image_response = await openai_client.images.generate(
    #         model="dall-e-3",
    #         prompt=image_prompt,
    #         size="1024x1024",
    #         quality="standard",
    #         n=1
    #         )
    #
    #     # Сохранение нового URL изображения
    #     image_url = image_response.data[0].url
    #     await bot.send_message(chat_id=chat_id, text="Генерация новой картинки: 100%")
    #
    #     # Отправка нового изображения пользователю
    #     await bot.send_message(chat_id=chat_id, text=f"({generate_text})\n\n[Изображение статьи]({image_url})", parse_mode="Markdown", reply_markup=get_inline_keyboard2())

    return generate_text


# Обработчик выбора /generate
async def generate_titles (callback_query: types.CallbackQuery, state: FSMContext):


    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id


    # news, image_url = await generate_news(callback_query)
    news = await top_titles (callback_query)


    json_news = json.loads(news)



    news = escape_markdown_v2(json_news)

    await state.update_data(news=json_news, message_id=message_id)

    # await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())
    await bot.edit_message_text(chat_id=chat_id,
        message_id=message_id,text=news,parse_mode="MarkdownV2",  reply_markup=get_delete_keyboard(json_news), disable_web_page_preview=True)


# Обработчик выбора "Сгенерировать заново"
# async def regenerate_news_handler(callback_query: types.CallbackQuery):
#     news, image_url = await generate_news(callback_query)
#
#     if news and image_url:
#     await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())


async def main():
    dp.message.register(command_start_handler, Command("start"))

    # dp.callback_query.register(generate_news_handler, lambda c: c.data == "change")
    dp.callback_query.register(generate_titles, lambda c: c.data == "generate")
    dp.callback_query.register(generate_news,  lambda c: c.data == "gen_news" )
    # dp.callback_query.register(regenerate_news_handler, lambda c: c.data == "regenderate")
    dp.callback_query.register(toggle_prompt_handler, lambda c: c.data == "toggle_prompt")
    # dp.callback_query.register(new_image_handler, lambda c: c.data == "new_image")

    await dp.start_polling(bot, on_shutdown=shutdown_handler)


if __name__ == "__main__":
    try:

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
