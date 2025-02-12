from aiog import *



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

def confirm_keyboard5():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Придумать новость", callback_data="gen_news")],
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

def yesorno():
    keyboard = (InlineKeyboardMarkup
    (inline_keyboard=[
    [InlineKeyboardButton(text="ДА", callback_data="yes")],
    [InlineKeyboardButton(text="нет", callback_data="no")]
    ])
    )

    return keyboard
