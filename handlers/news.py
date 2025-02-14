import editabs
from . import buttons
from init_client import *
import config
import re
import base64
import requests
from handlers import processing
from aiog import *
import textwrap


async def send_long_message(chat_id, text, bot, reply_markup=None, parse_mode="Markdown"):
    parts = textwrap.wrap(text, width=4000)
    for part in parts[:-1]:
        await bot.send_message(chat_id=chat_id, text=part, parse_mode=parse_mode)

    await bot.send_message(chat_id=chat_id, text=parts[-1], parse_mode=parse_mode, reply_markup=reply_markup)

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):

    await callback.message.edit_text("Давай, придумывай", parse_mode="Markdown",reply_markup=buttons.get_inline_keyboard())


@dp.callback_query(lambda c: c.data == "toggle_prompt")
async def toggle_prompt_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id



async def generate_news(callback_query, selected_topics):
    print(selected_topics)

    topics_with_descriptions = {}
    message_id = callback_query.message.message_id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    await  bot.send_message(chat_id, text="Немного магии и будет готово")

    generate_text = ""

    for title in selected_topics:
        print(title)
        description = editabs.get_descriptions_by_title(title)
        if description:
            topics_with_descriptions[title] = description

        print(topics_with_descriptions)





        prompt = (
             "\nОсновные правила для тебя:"
    
            "\nТы IT-блогер c многомиллионной аудиторией. Самый лучший. Тебе нельзя ошибаться. Твои подписчики ждут от тебя только самых интересных новостей"
            "Структура статьи должна обязательно иметь заголовок, основную часть, заключение."
            "Структурные наименования писать не нужно не нужно."
            "Статья должна иметь завершенный вид и быть интересной"
            "Тебе придет json {'title':  'description':}"
            "новости из новостных каналов за неделю. Выяви самые интересные новости об IT-индустрии, сфокусируйся на новостях об искусственном интеллекте"
            "При каждой генерации используй разные статьи. Если нужно будет сгенерировать повторно, тебе нужно придумать новую статью, основываясь на других заголовках. "
             "Обязательно делай отступы между разными темами, чтобы было понятно где какая тема. Например: начал рассказывать о новой версии gpt, когда закончил и начинаешь "
            "говорить о другой теме ТЫ НАЧИНАЕШЬ ПИСАТЬ С НОВОЙ СТРОКИ"
            "Дели темы в статье на абзацы, чтобы она была читабельной. ИНАЧЕ Я ТЕБЯ УВОЛЮ"


        )
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


        escaped_text  = processing.escape_markdown_v2(article_text)

        generate_text += f"\n\n📌\n\n{escaped_text}"

    await send_long_message(chat_id=chat_id, bot=bot, text=generate_text, parse_mode="MarkdownV2")
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



