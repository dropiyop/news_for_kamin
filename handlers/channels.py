from itertools import count

import aiogram.enums
from aiohttp import FormData

import editabs
from . import buttons
from . import topics
from init_client import *
import states
from handlers import processing
from aiog import *
import requests
from bs4 import BeautifulSoup
import re


def get_channel_name(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("meta", property="og:title")
    if title_tag:
        return title_tag["content"]
    return "Канал"


@dp.message(aiogram.F.text.lower() == "каналы")
async def button_channels(message: aiogram.types.Message, state=None, text=None) -> None:
    user_id = message.from_user.id
    channels = editabs.get_user_channels(user_id)

    if not channels:
        await message.answer(
            text="Список каналов пуст. Воспользуйтесь кнопкой ниже для добавления",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")]]))
        return

    channels_text = "\n".join(f"{i}\\. [{processing.convert_to_telegram_markdown(channel[1])}]({processing.convert_to_telegram_markdown(channel[0])})" for i, channel in enumerate(channels, start=1))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")],
        [InlineKeyboardButton(text="Удалить канал", callback_data=states.SelectDeleteCallback(count=','.join(str(el) for el in range(1, len(channels)+1))).pack())]
    ])

    await message.answer(
        text=f"*Список каналов:*\n\n{channels_text}",
        parse_mode="MarkdownV2",
        reply_markup=keyboard,
        disable_web_page_preview=True)

    await message.delete()


@dp.callback_query(aiogram.F.data == "add_channel")
async def add_channel_request(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="Можно много или одну ссылку в формате:\n`https://t.me/channel_name`",
        parse_mode="Markdown")


@dp.callback_query(aiogram.F.data == "cancel_remove")
async def add_channel_request(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=callback.message.md_text.replace("\nВыберите номер канала для удаления", ""),
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
        reply_markup=None)


@dp.callback_query(states.SelectDeleteCallback.filter())
async def add_channel_request(callback: types.CallbackQuery):
    callback_data = states.SelectDeleteCallback.unpack(callback.data)
    numbers = [int(el) for el in callback_data.count.split(",")]


    if len(numbers) == 1:
        channel_number = numbers[0]

        # Получаем ссылку на канал (если она нужна)
        link_remove = get_channel_link(callback.message.md_text, channel_number)

        # Удаляем канал из базы
        editabs.remove_user_channel(callback.message.chat.id, link_remove)

        # Отправляем подтверждение пользователю
        await callback.message.edit_text(
            text="Канал удалён! Список пуст. Воспользуйтесь кнопкой ниже для добавления.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")]
                    ]
                )
            )
        return

    builder = InlineKeyboardBuilder()
    row = []
    for i in numbers:
        row.append(InlineKeyboardButton(text=str(i), callback_data=states.DeleteCallback(number=i).pack()))

        if i % 8 == 0:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_remove"))


    await callback.message.edit_text(
        text=f"{callback.message.md_text}\n\nВыберите номер канала для удаления",
        parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2,
        reply_markup=builder.as_markup(),
        disable_web_page_preview=True)


def get_channel_link(message: str, index: int) -> str | None:
    """
    Ищет ссылки вида:
    1. [Название](https://t.me/...)
    2. [Название](https://t.me/...)
    и возвращает ту, которая под указанным порядковым номером (index).
    """
    lines = message.splitlines()  # Разбиваем на строки
    found_links = []

    # Проходим по каждой строке, убираем пробелы по краям
    for line in lines:
        line = line.strip()
        # Ищем шаблон:  "1. [Что-угодно](https://t.me/...)"
        match = re.match(r'^(\d+)\\\.\s+\[.*?\]\((https:\/\/t\.me\/[^\s)]+)\)$', line)
        if match:
            # group(1) — это порядковый номер, group(2) — это сама ссылка
            found_links.append((int(match.group(1)), match.group(2)))
    # Теперь у нас есть список кортежей: [(1, "https://..."), (2, "https://...") ...]
    # Нужно найти тот, у которого порядковый номер совпадает с `index`
    for (num, link) in found_links:
        if num == index:
            return link
    return None



def remove_channel_and_get_numbers(message: str, index: int):
    """
    Удаляет строку из message, которая начинается с заданного порядкового номера (index),
    и возвращает (обновленный текст, список оставшихся номеров).

    :param message: Исходный текст, где строки могут быть в любом порядке.
    :param index: Номер канала, который нужно удалить, например 3 (ищем строку, начинающуюся с "3.").
    :return: (updated_text, remaining_numbers)
    """
    lines = message.splitlines()  # Разбиваем на строки (сохраняем порядок)
    updated_lines = []

    print (lines)

    # Шаблон для поиска строки, которая начинается (без учёта пробелов) с "index." + пробел/конец
    # Пример: index=3 -> ищем "^ *3\. "
    pattern_remove = rf'^\s*{index}\\\.\s'

    # Проходимся по всем строкам и пропускаем лишь ту, что подходит под шаблон
    for line in lines:
        if re.match(pattern_remove, line):
            # Эту строку пропускаем (удаляем)
            continue
        updated_lines.append(line)

    # Собираем текст без удалённой строки
    updated_text = "\n".join(updated_lines)

    # Шаблон для нахождения всех номеров вида "5. " или "12. " в оставшихся строках
    pattern_nums = r'^\s*(\d+)\\\.\s'
    remaining_numbers = []

    for line in updated_lines:
        match = re.match(pattern_nums, line)
        if match:
            num = int(match.group(1))  # сам номер, например "5"
            remaining_numbers.append(num)

    return updated_text, remaining_numbers

@dp.callback_query(states.DeleteCallback.filter())
async def add_channel_request(callback: types.CallbackQuery):
    callback_data = states.DeleteCallback.unpack(callback.data)
    link_remove = get_channel_link(callback.message.md_text, callback_data.number)
    channels = [el[0] for el in editabs.get_user_channels(callback.message.chat.id)]

    if link_remove not in channels:
        await callback.answer("Канал уже удалён!", show_alert=True)
        return

    editabs.remove_user_channel(callback.message.chat.id, link_remove)
    update_text, list_numbers = remove_channel_and_get_numbers(callback.message.md_text, callback_data.number)
    if not list_numbers:
        await callback.message.edit_text(
            text="Список каналов пуст. Воспользуйтесь кнопкой ниже для добавления",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")]]))
        return

    builder = InlineKeyboardBuilder()


    row = []
    for number in list_numbers:
        row.append(InlineKeyboardButton(text=str(number), callback_data=states.DeleteCallback(number=number).pack()))

        if number % 8 == 0:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel_remove"))

    await callback.message.edit_text(text=update_text, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, reply_markup=builder.as_markup(), disable_web_page_preview=True)


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
        editabs.add_user_channel(user_id, channel, get_channel_name(channel))
        await topics.gen_titles_for_titles(channel, message.chat.id)

    # Формируем ответ
    response = "Добавлены каналы:\n" + "\n".join(f" {ch}" for ch in new_channels) if new_channels else ""


    if existing_channels:
        response += "\n!!! Эти каналы уже были в списке:\n" + "\n".join(f" {ch}" for ch in existing_channels)

    await message.reply(response or " Нет новых каналов для добавления.", disable_web_page_preview=True)


@dp.callback_query(lambda c: c.data == "back")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Сделай это снова", parse_mode="Markdown",reply_markup=buttons.get_inline_keyboard4())


@dp.callback_query(lambda c: c.data == "change")
async def edit_channels_menu(callback: types.CallbackQuery):


    await callback.message.edit_text("Действуй:", reply_markup= buttons.get_inline_keyboard4())
