import editabs
from Handlers import Buttons
from Init_client import *
import config
import re
import base64
import requests
from Handlers import processing, gen_titles, generate_news
from aiog import *

class Form(StatesGroup):
    waiting_for_contact = State()
    waiting_for_prompt = State()


init_clients = set()

async def send_welcome(message: types.Message):
    await message.reply("Готов для генерации новостей!", reply_markup=Buttons.get_inline_keyboard())
    
    
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
    await state.set_state(Form.waiting_for_contact)


def clean_phone_number(phone_number):
    cleaned_number = re.sub(r'\D', '', phone_number)
    return cleaned_number



@dp.message(Form.waiting_for_contact, F.content_type == "contact")
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
            url = config.CASCADE_USERS_URL
            credentials = f'{config.CASCADE_USER}:{config.CASCADE_PASSWORD}'
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




@dp.callback_query(lambda c: c.data.startswith("delete_topic_"))
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
        reply_markup=Buttons.get_delete_keyboard(news),
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
        parse_mode="MarkdownV2", reply_markup=Buttons.confirm_keyboard5(),
        disable_web_page_preview=True
    )

    await state.update_data(pending_function=generate_news.generate_news, formatted_news=formatted_news)


    # await state.clear()  #  Очищаем state после завершения




@dp.callback_query(lambda c: c.data == "generate_titles")
async def generate_titles(callback: types.CallbackQuery):

    await callback.message.edit_text("Я сделаю это и напишу как закончу",parse_mode="Markdown", reply_markup=Buttons.get_inline_keyboard3())
    await gen_titles.gen_titles(callback)  #






@dp.callback_query(lambda c: c.data == "add_channel")
async def add_channel_request(callback: types.CallbackQuery):
    """Сообщение о добавлении канала"""
    await callback.message.edit_text("Можно много или одну ссылку в формате:\n`https://t.me/channel_name`", parse_mode="Markdown",reply_markup=Buttons.back())



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

    await message.reply(response or " Нет новых каналов для добавления.", reply_markup=Buttons.back_or_titles(), disable_web_page_preview=True)


@dp.callback_query(lambda c: c.data == "list_channels")
async def list_channels(callback: types.CallbackQuery):
    user_id = callback.from_user.id  # Получаем user_id
    channels = editabs.get_user_channels(user_id)

    if not channels:
        await callback.message.edit_text("Список каналов пуст.", reply_markup=Buttons.back())
        return

    keyboard = InlineKeyboardBuilder()

    for i, channel in enumerate(channels, start=1):
        keyboard.button(text=f"Удалить {i}", callback_data=f"remove_channel:{channel}")

    keyboard.button(text="Назад", callback_data="back")
    keyboard.adjust(1)  # Каждая кнопка в отдельной строке

    channels_text = "\n".join(f"{i} {processing.escape_markdown(channel)}" for i, channel in enumerate(channels, start=1))
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

    await callback.message.edit_text("ТЫ УВЕРЕН?", parse_mode="Markdown",reply_markup=Buttons.yesorno())



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

    await callback.message.edit_text(" Все каналы успешно удалены!", parse_mode="Markdown", reply_markup=Buttons.get_inline_keyboard4())

@dp.callback_query(lambda c: c.data == "no")
async def remove_all_channels(callback: types.CallbackQuery):

    await callback.message.edit_text("ты не уверен", parse_mode="Markdown", reply_markup=Buttons.get_inline_keyboard4())


@dp.callback_query(lambda c: c.data == "back")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Сделай это снова", parse_mode="Markdown",reply_markup=Buttons.get_inline_keyboard4())




@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Давай, придумывай", parse_mode="Markdown",reply_markup=Buttons.get_inline_keyboard())




@dp.callback_query(lambda c: c.data == "change")
async def edit_channels_menu(callback: types.CallbackQuery):


    await callback.message.edit_text("Действуй:", reply_markup= Buttons.get_inline_keyboard4())


@dp.callback_query(lambda c: c.data == "toggle_prompt")
async def toggle_prompt_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id