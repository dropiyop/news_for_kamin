from Init_client import *
from Handlers import states, generate_news, gen_titles, top_titles
from  aiog import *
import asyncio

async def main():
    dp.message.register(states.command_start_handler, Command("start"))

    # dp.callback_query.register(generate_news_handler, lambda c: c.data == "change")
    # dp.callback_query.register(regenerate_news_handler, lambda c: c.data == "regenderate")
    # dp.callback_query.register(toggle_prompt_handler, lambda c: c.data == "toggle_prompt")
    # dp.callback_query.register(new_image_handler, lambda c: c.data == "new_image")

    await dp.start_polling(bot, on_shutdown=shutdown_handler)


if __name__ == "__main__":
    try:

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
