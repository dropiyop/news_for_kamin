from aiog import *


def get_bottom_buttons():
    keyboard = aiogram.types.ReplyKeyboardMarkup(
        keyboard=[[aiogram.types.KeyboardButton(text="Каналы"), aiogram.types.KeyboardButton(text="Темы недели")],
                   [aiogram.types.KeyboardButton(text="Удалить историю парсинга")]],
        resize_keyboard=True)

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

def parse_sevendays():
    keyboard = (InlineKeyboardMarkup
    (inline_keyboard=[
    [InlineKeyboardButton(text="Собрать темы за предыдущие 7 дней", callback_data="parse_sevendays")],

    ])
    )

    return keyboard


