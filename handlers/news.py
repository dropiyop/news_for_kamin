from numpy.ma.extras import unique

import editabs
from . import buttons
from init_client import *
import config
import re
import base64
import requests
from handlers import processing
from aiog import *


async def send_long_message(chat_id, text, bot, reply_markup=None, parse_mode="Markdown"):
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4096], reply_markup=reply_markup if i + 4096 >= len(text) else None,
                               parse_mode="Markdown",
                               disable_web_page_preview=True
                               )





async def generate_news(callback_query, selected_topics):

    topics_with_descriptions = {}
    unique_urls = {}
    message_id = callback_query.message.message_id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    await  bot.send_message(chat_id, text="Немного магии и будет готово")

    generate_text = ""

    for title in selected_topics:
        description = editabs.get_descriptions_by_title(title)

        for entry in description:
            unique_urls.setdefault(title, []).append(entry["url"])


        if description:
            topics_with_descriptions.setdefault(title, description)



    current_mode = editabs.get_user_mode(user_id)
    if current_mode == "ai":

        with open('promts/ai_news.md', 'r', encoding='utf-8') as file_ai:
            prompt_ai = file_ai.read()


        prompt = prompt_ai
        prompt += f"Description: {topics_with_descriptions}\n\n"


        response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "У тебя есть группа в социальной сети и ты должен придумывать по одной статье на основе предложенных  description. Ограничение на количество символов в статье строго 1500"},
            {"role": "user", "content": prompt}
            ],

        temperature=0.7,
        )

        # Получение текста из ответа
        article_text  = response.choices[0].message.content.strip()




        text = "\n\n".join(
            f"{title}:\n" + "\n".join(urls)
            for title, urls in unique_urls.items()
            )




        await send_long_message(chat_id=chat_id, bot=bot, text=article_text, parse_mode="Markdown")


    if current_mode == "hr":
        with open('promts/hr_news.md', 'r', encoding='utf-8') as file_hr:
            prompt_hr = file_hr.read()


        prompt = prompt_hr
        prompt += f"Description: {topics_with_descriptions}\n\n"

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "У тебя есть группа в социальной сети и ты должен придумывать по одной статье на основе предложенных  description. Ограничение на количество символов в статье строго 1500"},
                {"role": "user", "content": prompt}
                ],

            temperature=0.7,
            )

        # Получение текста из ответа
        article_text = response.choices[0].message.content.strip()

        print(article_text)

        text = "\n\n".join(
            f"{title}:\n" + "\n".join(urls)
            for title, urls in unique_urls.items()
            )

        print(text)

        await send_long_message(chat_id=chat_id, bot=bot, text=article_text, parse_mode="Markdown")


        # print(prompt)


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

    # await bot.edit_message_text(chat_id=callback_query.message.chat.id,
    # message_id=callback_query.message.message_id,
    # text=callback_query.message.text, reply_markup=None, disable_web_page_preview=True)



