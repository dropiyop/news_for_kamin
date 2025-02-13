import editabs
from . import buttons
from init_client import *
import config
import re
import base64
import requests
from handlers import processing
from aiog import *


@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Давай, придумывай", parse_mode="Markdown",reply_markup=buttons.get_inline_keyboard())


@dp.callback_query(lambda c: c.data == "toggle_prompt")
async def toggle_prompt_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id


@dp.callback_query(lambda c: c.data ==  "gen_news" )
async def generate_news(callback_query, state: FSMContext):
    global generate_text, user_prompts
    user_prompts = set()
    message_id = callback_query.message.message_id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    user_data = await state.get_data()

    topics_with_descriptions = user_data


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

    generate_text = processing.escape_markdown_v2(generate_text)

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

    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
    message_id=callback_query.message.message_id,
    text=callback_query.message.text, reply_markup=None, disable_web_page_preview=True)

    await bot.send_message(chat_id=chat_id, text=generate_text, parse_mode="MarkdownV2", reply_markup=buttons.get_inline_keyboard3(), disable_web_page_preview=True)
