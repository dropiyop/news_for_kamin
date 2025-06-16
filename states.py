from aiog import *
import aiogram.filters.callback_data


class Form(StatesGroup):
    waiting_for_contact = State()
    waiting_for_prompt = State()


class SelectDeleteCallback(aiogram.filters.callback_data.CallbackData, prefix="seldel"):
    count: str

class DeleteCallback(aiogram.filters.callback_data.CallbackData, prefix="del"):
    number: int

class ChooseCallback(aiogram.filters.callback_data.CallbackData, prefix="choose"):
    n: int
    c: int
    chosen_id: str
    page: int
    gen_id: int

class ModeCallback(aiogram.filters.callback_data.CallbackData, prefix="mode"):
    mode: str = None

class GenerateCallback(aiogram.filters.callback_data.CallbackData, prefix="generate"):
    chosen_id: str

class NumberPageCallback(aiogram.filters.callback_data.CallbackData, prefix="page"):
    page: int
    chosen_id: str
    gen_id: int

class GroupCallback(aiogram.filters.callback_data.CallbackData, prefix="group"):
    gen_id: int
    page: int
    chosen_id: str

class SubtopicCallback(aiogram.filters.callback_data.CallbackData, prefix="sub"):
    group_id: int
    subtopic_id: int

class BackCallback(aiogram.filters.callback_data.CallbackData, prefix="back_to_groups"):
    chosen_id: str

