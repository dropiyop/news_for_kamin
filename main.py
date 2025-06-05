#!/usr/bin/env python3.12

from init_client import *
from handlers import *
from handlers import shedule
from  aiog import *
import asyncio
import  logging

logging.basicConfig(level=logging.INFO)

async def main():
    shedule.prepare_schedulers()
    shedule.delete_history()
    await dp.start_polling(bot,
                           on_shutdown=shutdown_handler,
                           drop_pending_updates=True)

if __name__ == "__main__":
    try:

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
