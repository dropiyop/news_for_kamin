from aiog import *
import aiogram.filters.callback_data


class Form(StatesGroup):
    waiting_for_contact = State()
    waiting_for_prompt = State()


class SelectDeleteCallback(aiogram.filters.callback_data.CallbackData, prefix="seldel"):
    count: str

class DeleteCallback(aiogram.filters.callback_data.CallbackData, prefix="del"):
    number: int

class ChooseCallback(aiogram.filters.callback_data.CallbackData, prefix="c"):
    n: int
    c: int
    ch: str

class GenerateCallback(aiogram.filters.callback_data.CallbackData, prefix="generate"):
    choose: str
