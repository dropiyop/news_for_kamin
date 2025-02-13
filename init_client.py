from aiog import *
import config
import httpx
import httpx_socks
import openai
import os




dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=config.TELEGRAM_TOKEN)

async def shutdown_handler(bot):
    await bot.session.close()


transport = httpx_socks.AsyncProxyTransport.from_url(f"socks5://{os.getenv('PROXY_URL')}:{os.getenv('PROXY_PORT')}")
http_client = httpx.AsyncClient(transport=transport)
openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_TOKEN'), http_client=http_client)

