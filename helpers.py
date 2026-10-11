import os
import logging
from aiogram import Bot, BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, FSInputFile, TelegramObject
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS, REQUIRED_CHANNEL, REQUIRED_CHANNEL_LINK, START_PHOTO 
from texts import TEXTS
from keyboards import subscription_kb
from emojis import E
from database import is_user_banned

class BanMiddleware(BaseMiddleware):
    """Мидлварь для полной блокировки доступа заблокированным пользователям."""
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user and user.id not in ADMIN_IDS:
            if is_user_banned(user.id):
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer("⛔ Вы заблокированы в боте.", show_alert=True)
                    except Exception:
                        pass
                elif isinstance(event, Message):
                    try:
                        await event.answer(
                            f"{E['cross']} <b>Ваш аккаунт заблокирован администратором.</b>",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                return
        return await handler(event, data)

async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Проверяет подписку пользователя на обязательный канал."""
    if user_id in ADMIN_IDS:
        return True
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        )
    except Exception as e:
        logging.warning(f"Ошибка проверки подписки: {e}")
        return False

async def force_subscribe(event: Message | CallbackQuery, bot: Bot) -> bool:
    """Проверяет подписку. Если не подписан — отправляет уведомление и возвращает False."""
    user_id = event.from_user.id
    if user_id not in ADMIN_IDS and is_user_banned(user_id):
        try:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Вы заблокированы в боте.", show_alert=True)
            else:
                await event.answer(f"{E['cross']} <b>Ваш аккаунт заблокирован администратором.</b>", parse_mode="HTML")
        except Exception:
            pass
        return False

    if await is_subscribed(bot, user_id):
        return True

    text = TEXTS["sub_required"].format(REQUIRED_CHANNEL_LINK)
    kb = subscription_kb()

    try:
        if isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
            await event.answer()
        else:
            await event.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logging.warning(f"force_subscribe notice error: {e}")
    return False

async def send_start_message(msg: Message, text: str, kb: InlineKeyboardMarkup):
    """Отправляет стартовое приветственное сообщение с фото."""
    if START_PHOTO:
        try:
            if os.path.exists(START_PHOTO):
                photo = FSInputFile(START_PHOTO)
            else:
                photo = START_PHOTO
            await msg.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception as e:
            logging.warning(f"Не удалось отправить фото: {e}")
    await msg.answer(text, reply_markup=kb, parse_mode="HTML")

async def safe_edit(msg: Message, text: str, kb: InlineKeyboardMarkup = None):
    """Безопасно редактирует сообщение (текст или подпись к фото) без дублирования."""
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
        else:
            await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return
        try:
            await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    except Exception:
        try:
            await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass

def ordinal_ru(n: int) -> str:
    return f"№{n}"
