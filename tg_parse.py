import os
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import ChannelInvalidError, ChannelPrivateError, ChannelTooBigError
from telethon.tl.types import PeerChannel
import dotenv
import asyncio


dotenv.load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
phone = os.getenv('phone')


client = TelegramClient(phone, api_id, api_hash)


async def fetch_messages_by_date(chat_id,days):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days)

    messages = []
    offset_id = 0  # Начинаем с последнего сообщения
    limit = 10  # Количество сообщений за один запрос

    while True:
        history = await client(GetHistoryRequest(
            peer=chat_id,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0

            ))



        if not history.messages:
            break

        for message in history.messages:
            # Проверяем, входит ли сообщение в указанный диапазон дат
            if start_date <= message.date < end_date:
                messages.append(message)
            elif message.date < start_date:
                # Если достигли сообщений до нужной даты, останавливаем цикл
                return messages

        # Обновляем offset_id для следующего запроса
        offset_id = history.messages[-1].id

    return messages


async def parse(url_channel,days):

    async with client:
        try:
            # Получаем entity (объект чата)
            entity = await client.get_entity(url_channel)

            # Получаем сообщения
            messages = await fetch_messages_by_date(entity,days)
            return messages

        except ChannelInvalidError:
            return " Ошибка: Некорректная ссылка на канал."
        except ChannelPrivateError:
            return " Ошибка: Канал приватный. Подключите бота к нему."
        except ChannelTooBigError:
            return " Ошибка: Канал не найден. Проверьте URL."
        except ValueError:
            return "Ошибка: Не удалось найти канал. Возможно, URL неверный."
        except Exception as e:
            return f"Неизвестная ошибка: {str(e)}"





        #
        # # Печатаем сообщения
        # for message in messages:
        #
        #     print(f"{message.date}: {message.message}")




#
# # Запускаем основной процесс
# chat_id = "https://t.me/cgevent"  # Укажите нужный ID чата
#
# asyncio.run(parse(chat_id,days))



