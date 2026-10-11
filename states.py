from aiogram.fsm.state import State, StatesGroup

class WithdrawState(StatesGroup):
    waiting_amount = State()

class ServiceState(StatesGroup):
    waiting_phone = State()
    waiting_photo = State()

class CodeState(StatesGroup):
    waiting_code = State()

class ReplyState(StatesGroup):
    waiting_text = State()

class AdminReplyState(StatesGroup):
    waiting_text = State()

class BroadcastState(StatesGroup):
    waiting_text = State()
    confirm_text = State()

class AdminState(StatesGroup):
    waiting_user_id = State()
    waiting_amount  = State()

class AdminBanState(StatesGroup):
    waiting_user_id = State()

class OpAddState(StatesGroup):
    waiting_name   = State()
    waiting_code   = State()
    waiting_price  = State()
    waiting_reward = State()

class OpEditState(StatesGroup):
    waiting_field = State()
    waiting_value = State()

class OpEmojiState(StatesGroup):
    waiting_emoji = State()
