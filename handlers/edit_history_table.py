import aiogram.enums

import editabs
from init_client import *
from . import buttons, processing, tg_parse, news
from . import news as package_news
# from handlers import processing, tg_parse, news
from aiog import *
import chat
import pandas
import states
import re



@dp.message(aiogram.F.text.lower() == "удалить историю парсинга")
async def delete_buttons(message: aiogram.types.Message) -> None:

    user_id =  message.from_user.id

    await bot.send_message(chat_id=user_id, text="Вы уверены???", reply_markup=buttons.yesorno())




@dp.callback_query(lambda c: c.data == "yes")
async def yes(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    editabs.delete_chat_history(user_id)
    await bot.send_message(chat_id=user_id, text= "Вы удалили историю")



@dp.callback_query(lambda c: c.data == "no")
async def yes(callback: types.CallbackQuery):

    user_id = callback.from_user.id
    await bot.send_message(chat_id=user_id, text="Вы не уверены")



