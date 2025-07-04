import re
import logging
import asyncio
import chat
import editabs
from init_client import *
from dotenv import load_dotenv
from handlers import  processing

# Загрузка переменных окружения из .env (если используется)
load_dotenv()

MAX_MESSAGE_LENGTH = 4096
SAFE_SPLIT_LENGTH = 4000

# Функция предварительной обработки текста
def preprocess_text(text: str) -> str:
    # Удаление лишних пробелов и переходов строки
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Здесь можно добавить дополнительные шаги (удаление эмодзи, ссылок и т.д.)
    return cleaned


def split_by_sentences(text: str, max_length: int) -> list[str]:
    """
    Разбивает текст по предложениям, если он слишком длинный.
    """
    # Простое разбиение по точкам, восклицательным и вопросительным знакам
    sentences = re.split(r'(?<=[.!?])\s+', text)

    parts = []
    current_part = ""

    for sentence in sentences:
        if len(current_part + sentence + ' ') <= max_length:
            current_part += sentence + ' '
        else:
            if current_part.strip():
                parts.append(current_part.strip())

            # Если предложение слишком длинное, разбиваем по словам
            if len(sentence) > max_length:
                word_parts = split_by_words(sentence, max_length)
                parts.extend(word_parts[:-1])  # Все части кроме последней
                current_part = word_parts[-1] + ' '  # Последняя часть становится началом следующей
            else:
                current_part = sentence + ' '

    if current_part.strip():
        parts.append(current_part.strip())

    return parts


def split_by_words(text: str, max_length: int) -> list[str]:
    """
    Разбивает текст по словам как последний вариант.
    """
    words = text.split(' ')
    parts = []
    current_part = ""

    for word in words:
        if len(current_part + word + ' ') <= max_length:
            current_part += word + ' '
        else:
            if current_part.strip():
                parts.append(current_part.strip())
            current_part = word + ' '

    if current_part.strip():
        parts.append(current_part.strip())

    return parts


def split_message(text: str, max_length: int = SAFE_SPLIT_LENGTH) -> list[str]:
    """
    Разбивает текст на части, не превышающие max_length символов.
    Старается разбивать по предложениям, абзацам или словам.
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    # Разбиваем по абзацам
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # Если абзац помещается в текущую часть
        if len(current_part + paragraph + '\n\n') <= max_length:
            current_part += paragraph + '\n\n'
        else:
            # Сохраняем текущую часть, если она не пустая
            if current_part.strip():
                parts.append(current_part.strip())
                current_part = ""

            # Если абзац слишком длинный, разбиваем его
            if len(paragraph) > max_length:
                sentences = split_by_sentences(paragraph, max_length)
                for sentence in sentences:
                    if len(current_part + sentence) <= max_length:
                        current_part += sentence
                    else:
                        if current_part.strip():
                            parts.append(current_part.strip())
                        current_part = sentence
            else:
                current_part = paragraph + '\n\n'

    # Добавляем последнюю часть
    if current_part.strip():
        parts.append(current_part.strip())

    return parts

# Асинхронная функция для отправки длинного сообщения с разбиением
async def send_long_message(message: Message, text: str):
    """
    Отправляет длинное сообщение, разбивая его на части при необходимости.
    """

    text = processing.escape_markdown_v2(text)

    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.answer(text, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        return

    # Разбиваем сообщение на части
    parts = split_message(text)

    # Отправляем каждую часть
    for i, part in enumerate(parts):
        try:
            if i == 0:
                await message.answer(part, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
            else:
                # Добавляем небольшую задержку между сообщениями
                await asyncio.sleep(0.1)
                await message.answer(part, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Error sending message part {i + 1}: {e}")
            await message.answer(f"Ошибка при отправке части {i + 1} сообщения.")


# Функция для проверки наличия ссылок в тексте
def contains_url(text: str) -> bool:
    """Проверяет, содержит ли текст URL-адреса"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return bool(re.search(url_pattern, text))


# Асинхронная функция для отправки запроса в OpenAI и получения ответа
async def query_openai(user_mes: str,user_id) -> str:
    print(user_id)
    current_mode = editabs.get_user_mode(user_id)

    if current_mode == 'hr':
        with open('promts/hr_news.md', 'r', encoding='utf-8') as file:
            prompt_hr = file.read()
            prompt_hr += user_mes

            print(prompt_hr)

        # Создаем историю сообщений
        chat_messages = chat.MessageHistory()

        # Добавляем системное сообщение
        chat_messages.add_message(
            role=chat.Message.ROLE_SYSTEM,
            content=prompt_hr
            )

        # Добавляем пользовательское сообщение
        chat_messages.add_message(
            role=chat.Message.ROLE_USER,
            content=user_mes
            )

        # Выбираем модель в зависимости от наличия ссылок
        model = "gpt-4o-mini-search-preview" if contains_url(user_mes) else "gpt-4o-mini"

        logging.info(f"Using model: {model}")
        if model == "gpt-4o-mini":

            response = await openai_client.chat.completions.create(
                model=model,
                messages=chat_messages.to_api_format(),
                temperature=0.4)

            print(response)

            return response.choices[0].message.content
        else:

            response = await openai_client.chat.completions.create(
                model=model,
                messages=chat_messages.to_api_format())
            print(response)

            return response.choices[0].message.content


    if current_mode == 'ai':
        with open('promts/ai_news.md', 'r', encoding='utf-8') as file:
            prompt = file.read()
            prompt += user_mes

            print(prompt)

        # Выбираем модель в зависимости от наличия ссылок
        model = "gpt-4o-mini-search-preview" if contains_url(user_mes) else "gpt-4o-mini"

        logging.info(f"Using model: {model}")

        response = await openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
            )
        return response.choices[0].message.content


# Обработчик входящих сообщений
@dp.message()
async def handle_message(message: Message):
    user_text = message.text or ""
    user_id = message.from_user.id

    # Предобработка текста пользователя
    processed = preprocess_text(user_text)
    logging.info(f"Processed user text: {processed}")

    # Отправка в GPT и получение ответа
    try:
        gpt_response = await query_openai(processed,user_id)
    except Exception as e:
        logging.error(f"Error querying OpenAI: {e}")
        await message.reply("Извините, не удалось получить ответ от GPT.")
        return

    # Отправка ответа в Telegram
    await send_long_message(message, gpt_response)