from Init_client import *
import editabs
import json
from Handlers import processing
from Handlers import Buttons


@dp.callback_query(lambda c: c.data == "generate")
async def top_titles(callback_query,state: FSMContext):

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    history  = editabs.get_chat_history(user_id,role="assistant", title=1)

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Выяви из этих заголовков часто повторяющиеся. В ответе предоставь title и url"
             },
            {"role": "user", "content": f"Description: {history}\n\n Выяви из этих заголовков часто повторяющиеся и в ответе предоставь топ 5 по убыванию.  В ответе предоставь title и url"}
            ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "titles",
                "schema": {
                    "type": "object",
                    "properties": {
                        "topics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "url": {"type": "string"}
                                    },
                                "required": ["id", "title",  "url"],
                                "additionalProperties": False
                                }
                            }
                        },
                    "required": ["topics"],
                    "additionalProperties": False
                    },
                "strict": True
                }
            },
        temperature=0.4
        )

    response_json = json.loads(response.choices[0].message.content)

    topics_with_descriptions = json.dumps([
        {
            "id": topic.get("id"),
            "title": topic.get("title"),
            "url": topic.get("url"),
            "description": editabs.get_description_by_url(topic.get("url", "")) or "Описание не найдено"
            }
        for topic in response_json.get("topics", [])
        ], ensure_ascii=False, indent=4)

    print (topics_with_descriptions)


    json_news = json.loads(topics_with_descriptions)

    news = processing.escape_markdown_v2(json_news)

    await state.update_data(news=json_news, message_id=message_id)

    # await send_long_message(chat_id=callback_query.message.chat.id, text=f"{news}\n\n[Изображение статьи]({image_url})", bot=callback_query.bot, reply_markup=get_inline_keyboard2())
    await bot.edit_message_text(chat_id=chat_id,
                                message_id=message_id, text=news, parse_mode="MarkdownV2", reply_markup=Buttons.get_delete_keyboard(json_news), disable_web_page_preview=True)

