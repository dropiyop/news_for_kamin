from init_client import *
from handlers import *
from handlers import shedule
from  aiog import *
import asyncio

async def main():
    shedule.prepare_schedulers()
    shedule.delete_history()
    await dp.start_polling(bot, on_shutdown=shutdown_handler)

if __name__ == "__main__":
    try:

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
