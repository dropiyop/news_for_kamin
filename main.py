import openai
import tg_parse
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
import re
import random
import json
import requests
from aiogram.fsm.context import FSMContext
from aiogram import F
import base64
import states
from aiogram import types
import os
import dotenv
import httpx
import httpx_socks
from database import  get_connection
import sqlite3


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

def add_init_client(user_id,contact_username,contact_name,contact_phone):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
          INSERT OR IGNORE INTO init_clients (user_id, contact_username, contact_name, contact_phone) 
          VALUES (?, ?, ?, ?)
      """, (user_id, contact_username, contact_name, contact_phone))

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





dotenv.load_dotenv()

flag = False
# Объявление глобальных переменных
generate_text = None,
image_url = None


init_clients = set()  # Инициализация списка для хранения данных пользователей
used_titles = set()  # Инициализация списка для хранения использованных заголовков
user_prompts = {}






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
used_titles = set()


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
                        add_init_client(contact_id, contact_username, contact_name, contact_phone)
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

def back():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back")]
        ])

    return keyboard


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
    new_channels = valid_channels - set(get_user_channels(user_id))
    existing_channels = valid_channels & set(get_user_channels(user_id))

    # Добавляем новые каналы в базу данных
    for channel in new_channels:
        add_user_channel(user_id, channel)


    # Формируем ответ
    response = "Добавлены каналы:\n" + "\n".join(f" {ch}" for ch in new_channels) if new_channels else ""
    if existing_channels:
        response += "\n!!! Эти каналы уже были в списке:\n" + "\n".join(f" {ch}" for ch in existing_channels)

    await message.reply(response or " Нет новых каналов для добавления.", reply_markup=back(), disable_web_page_preview=True)


def escape_markdown(text: str) -> str:
    """Экранирует специальные символы MarkdownV2"""
    escape_chars = r"_*[]()~`>#+-=|{}.!<>"
    return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", text)


@dp.callback_query(lambda c: c.data == "list_channels")
async def list_channels(callback: types.CallbackQuery):
    user_id = callback.from_user.id  # Получаем user_id
    channels = get_user_channels(user_id)

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

    channels = get_user_channels(user_id)

    channel = callback.data.replace("remove_channel:", "")

    if channel not in channels:
        await callback.answer("Канал уже удалён!", show_alert=True)
        return

    remove_user_channel(user_id,channel)


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

    channels = get_user_channels(user_id)

    if not channels:
        await callback.answer("Список каналов пуст", show_alert=True)
        return

    # Удаляем все каналы пользователя из базы данных
    all_remove_channels(user_id)

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

async def generate_news(callback_query):
    global generate_text, image_url, used_titles, user_prompts
    message_id = callback_query.message.message_id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    # Проверяем, существует ли пользовательский промпт
    if user_id in user_prompts:
        # Используем промпт, заданный пользователем
        prompt = (user_prompts[user_id] + "\nОсновные правила для тебя:"
                                          "\n1.Всего в статье должно быть 900 символов. НИКОГДА НЕ МОЖЕТ БЫТЬ БОЛЬШЕ 900 СИМВОЛОВ."
                                          "\n2.Структура статьи должна обязательно иметь заголовок, основную часть, заключение."
                                          "\n3.Структурные наименования писать не нужно не нужно."
                                          "\n4.Статья должна иметь завершенный вид и быть интересной"
                                          "\nОграничение на количество символов статьи = 900"
                                          "\nНе включай ссылки в свои статьи"
                  )
    else:

        channels = get_user_channels(user_id)

        url_channel = random.choice(channels)

        try:
            messages = await tg_parse.parse(url_channel)

            if isinstance(messages, str):  # Если функция вернула строку (ошибка)
                await bot.send_message(chat_id, messages)  # Отправляем пользователю сообщение об ошибке
            else:
                # Обрабатываем полученные сообщения
                for msg in messages:
                    print(msg)

        except Exception as e:
            await bot.send_message(chat_id, f"🚨 Ошибка при парсинге: {str(e)}")



        new_titles = [
            (msg.date)
            for msg in messages

            if str(msg.date) not in used_titles  # Проверяем, использовался ли заголовок (дата)
            ]



        if not new_titles:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Нет новых статей для генерации.")
            return None

        await bot.send_message(chat_id=chat_id, text="Генерация новости: 20%")

        # selected_description = random.choice(title_description)
        print (title_description)
        used_titles.add(str(msg.date))
        print(used_titles)
        save_used_titles()

        prompt = (
            "\nОсновные правила для тебя:"
            "1.Всего в статье должно быть 900 символов. НИКОГДА НЕ МОЖЕТ БЫТЬ БОЛЬШЕ 900 СИМВОЛОВ.  2.Структура статьи должна обязательно иметь заголовок, основную часть, заключение."
            "3.Структурные наименования писать не нужно не нужно."
            "4.Статья должна иметь завершенный вид и быть интересной"
            "Напиши одну IT-статью (Всего в статье должно быть 900 символов, ИНАЧЕ Я ТЕБЯ УВОЛЮ) на основе заголовков и описаний, которые придут тебе из RSS ленты. Ограничение на количество символов статьи = 900"
            "При каждой генерации используй разные статьи. Если нужно будет сгенерировать повторно, тебе нужно придумать новую статью, основываясь на других заголовках. "
            "Всегда рандомно выбирай статьи. Суммаризируй весь текст ровно до 900 символов.  Не включай ссылки в свои статьи\n\n"
        )
        prompt += f"Description: {selected_description}\n\n"
        prompt += "На основе этих заголовков и описаний напиши одну статью. НЕ БОЛЬШЕ ВСЕГО 900 СИМВОЛОВ, ИНАЧЕ Я ТЕБЯ УВОЛЮ. Если нужно будет сгенерировать повторно, используй другие заголовки и описания. Ограничение на количество символов статьи = 900. Не включай ссылки в свои статьи."

    await bot.send_message(chat_id=chat_id, text="Генерация новости: 50%")

    # response = openai.ChatCompletion.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "У тебя есть группа в социальной сети и ты должен придумывать по одной статье на основе предложенных title и description. Ограничение на количество символов в статье строго 900"},
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=1000,
    #     temperature=0.7,
    # )



    response =  openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "У тебя есть группа в социальной сети и ты должен придумывать по одной статье на основе предложенных title и description. Ограничение на количество символов в статье строго 900"},
            {"role": "user", "content": prompt}
            ],
        max_tokens=1000,
        temperature=0.7,
        )

    # Получение текста из ответа
    generate_text = response.choices[0].message.content.strip()
    print(prompt)
    await bot.send_message(chat_id=chat_id, text="Генерация новости: 70%")

    # Генерация изображения на основе текста статьи
    image_prompt = f"Create an illustration for the following article: {generate_text}"
    image_response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1
        )

    image_url = image_response.data[0].url
    await bot.send_message(chat_id=chat_id, text="Генерация новости: 100%")

    return generate_text, image_url


@dp.callback_query(lambda c: c.data == "new_image")
async def new_image_handler(callback_query: types.CallbackQuery):
    global generate_text, image_url

    chat_id = callback_query.message.chat.id

    # Проверяем, определен ли текст статьи
    if not generate_text:
        await callback_query.message.reply("Ошибка: текст статьи не найден. Пожалуйста, сгенерируйте новость сначала.")
        return

    await bot.send_message(chat_id=chat_id, text="Генерация новой картинки: 20%")

    # Генерация изображения на основе уже сгенерированного текста статьи
    image_prompt = f"Create an illustration for the following article: {generate_text}"
    image_response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1
        )

    # Сохранение нового URL изображения
    image_url = image_response.data[0].url
    await bot.send_message(chat_id=chat_id, text="Генерация новой картинки: 100%")

    # Отправка нового изображения пользователю
    await bot.send_message(chat_id=chat_id, text=f"({generate_text})\n\n[Изображение статьи]({image_url})", parse_mode="Markdown", reply_markup=get_inline_keyboard2())

    return generate_text, image_url





async def send_telegram_message(chat_id, text, reply_markup=None, bot=None):
    # Используем асинхронный метод для отправки сообщения в Telegram
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)



async def send_long_message(chat_id, text, bot, reply_markup=None):
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4096], reply_markup=reply_markup if i + 4096 >= len(text) else None, parse_mode="Markdown")


async def send_welcome(message: types.Message):
    await message.reply("Готов для генерации новостей!", reply_markup=get_inline_keyboard())


# Обработчик выбора /generate
async def generate_news_handler(callback_query: types.CallbackQuery):
    news, image_url = await generate_news(callback_query)

    await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())


# Обработчик выбора "Сгенерировать заново"
async def regenerate_news_handler(callback_query: types.CallbackQuery):
    news, image_url = await generate_news(callback_query)

    if news and image_url:
        await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())


async def main():
    dp.message.register(command_start_handler, Command("start"))

    dp.callback_query.register(generate_news_handler, lambda c: c.data == "change")
    dp.callback_query.register(generate_news_handler, lambda c: c.data == "generate")
    dp.callback_query.register(regenerate_news_handler, lambda c: c.data == "regenerate")
    # dp.callback_query.register(publish_news_handler, lambda c: c.data == "publish")
    dp.callback_query.register(toggle_prompt_handler, lambda c: c.data == "toggle_prompt")
    dp.callback_query.register(new_image_handler, lambda c: c.data == "new_image")

    await dp.start_polling(bot, on_shutdown=shutdown_handler)


if __name__ == "__main__":
    try:

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
