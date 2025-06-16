from aiog import *
import asyncio
from handlers import user_mode
from init_client import *
import editabs
from simple_tg_md import convert_to_md2




def create_progress_bar_slider(current_days: int) -> InlineKeyboardMarkup:

    # Создаем прогресс-бар
    progress_length = 10
    filled_length = current_days

    progress_bar = ""
    for i in range(1, progress_length + 1):
        if i <= filled_length:
            progress_bar = "█" * current_days + "░" * (progress_length - current_days)

    # Процент заполнения

    header = f"📆 Дни: {current_days}/10"

    # Ряд с прогресс-баром
    progress_row = [InlineKeyboardButton(text=f"[{progress_bar}]", callback_data="progress_visual")]

    # Кнопки изменения
    control_row = [
        InlineKeyboardButton(text="⬅️", callback_data=f"progress_dec:{current_days}"),
        InlineKeyboardButton(text="➡️", callback_data=f"progress_inc:{current_days}")
        ]

    # Быстрые значения
    quick_row1 = [
        InlineKeyboardButton(text="1", callback_data="progress_set:1"),
        InlineKeyboardButton(text="3", callback_data="progress_set:3"),
        InlineKeyboardButton(text="5", callback_data="progress_set:5"),
        InlineKeyboardButton(text="7", callback_data="progress_set:7"),
        InlineKeyboardButton(text="10", callback_data="progress_set:10")
        ]

    # Подтверждение

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=header, callback_data="progress_header")],
        progress_row,
        control_row
        ])

    return keyboard


@dp.callback_query(F.data == "mode_days")
async def cmd_progress_slider(callback: CallbackQuery):
    user_id = callback.from_user.id
    days = editabs.get_user_days(user_id)  # Получаем текущее значение из БД

    keyboard = create_progress_bar_slider(days)
    await callback.message.edit_text(convert_to_md2( "*Выбор количества дней*\n\n"
        "_количество дней за которые будут просматриваться новости из добавленных телеграмм каналов_\n\n"
        "Используйте стрелки для настройки от 1 до 10 дней:")
       ,
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
        )
    await callback.answer()



@dp.callback_query(F.data.startswith("progress_inc:"))
async def process_progress_increase(callback: CallbackQuery):
    current_value = int(callback.data.split(":")[1])
    new_value = min(10, current_value + 1)
    user_id = callback.from_user.id

    editabs.save_user_days(user_id, new_value)  # сохраняем в БД

    keyboard = create_progress_bar_slider(new_value)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"{new_value}")


@dp.callback_query(F.data.startswith("progress_dec:"))
async def process_progress_decrease(callback: CallbackQuery):
    current_value = int(callback.data.split(":")[1])
    new_value = max(1, current_value - 1)
    user_id = callback.from_user.id

    editabs.save_user_days(user_id, new_value)  # сохраняем в БД

    keyboard = create_progress_bar_slider(new_value)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"{new_value}")



@dp.callback_query(F.data.startswith("progress_set:"))
async def process_progress_set(callback: CallbackQuery):
    new_value = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    editabs.save_user_days(user_id, new_value)  # сохраняем в БД

    keyboard = create_progress_bar_slider(new_value)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"⚡ Установлено: {new_value}")





@dp.callback_query(F.data.in_(["progress_header", "progress_visual", "progress_current"]))
async def process_info_buttons(callback: CallbackQuery):
    """Обработка информационных кнопок"""
    await callback.answer()


@dp.callback_query(F.data == "show_days")
async def cmd_show_days(callback: CallbackQuery):
    """Показать текущее значение days (из БД)"""
    user_id = callback.from_user.id
    days = editabs.get_user_days(user_id)

    if isinstance(days, int):
        progress_bar = "█" * days + "░" * (10 - days)
        percentage = (days / 10) * 100

        await callback.message.answer(
            f"📅 Текущее значение days: <b>{days}</b>\n"
            f"Прогресс: [{progress_bar}] {percentage:.0f}%",
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("Значение не установлено. Выберите через меню.")
    await callback.answer()
