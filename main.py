from init_client import *
from handlers import *
from  aiog import *
import asyncio

async def main():
    await dp.start_polling(bot, on_shutdown=shutdown_handler)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
