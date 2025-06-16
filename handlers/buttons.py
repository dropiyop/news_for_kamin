import editabs
from aiog import *
import states

def get_bottom_buttons():
   keyboard = aiogram.types.ReplyKeyboardMarkup(
       keyboard=[[aiogram.types.KeyboardButton(text="Каналы"), aiogram.types.KeyboardButton(text="Темы недели")],
                 [aiogram.types.KeyboardButton(text="Удалить историю парсинга"), aiogram.types.KeyboardButton(text="настройки")]],
       resize_keyboard=True)

   return keyboard

def mode_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Добавляем первый ряд с двумя кнопками
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🤖 AI Режим",
            callback_data=states.ModeCallback(mode="ai").pack()
            ),
        InlineKeyboardButton(
            text="👥 HR Режим",
            callback_data=states.ModeCallback(mode="hr").pack()
            )
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



def yesorno():
    keyboard = (InlineKeyboardMarkup
    (inline_keyboard=[
    [InlineKeyboardButton(text="ДА", callback_data="yes")],
    [InlineKeyboardButton(text="нет", callback_data="no")]
    ])
    )

    return keyboard

def parse_sevendays(user_id):
    days = editabs.get_user_days(user_id)
    keyboard = (InlineKeyboardMarkup
    (inline_keyboard=[
    [InlineKeyboardButton(text=f"Собрать темы за предыдущие {days} дней", callback_data="parse_sevendays")],

    ])
    )

    return keyboard


