from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    waiting_for_contact = State()
    waiting_for_prompt = State()  # Добавьте это новое состояние для ввода промпта
    
