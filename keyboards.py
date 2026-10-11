from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_LINK, REQUIRED_CHANNEL_LINK 
from emojis import MENU_EMOJIS, OPERATOR_EMOJIS

def _btn(text: str, emoji_key: str = None, **kwargs) -> InlineKeyboardButton:
    """Создаёт инлайн-кнопку с прикреплением премиум-эмодзи (icon_custom_emoji_id), если доступно."""
    kw = {"text": text, **kwargs}
    if emoji_key:
        eid = MENU_EMOJIS.get(emoji_key) or ""
        if eid:
            kw["icon_custom_emoji_id"] = str(eid)
    return InlineKeyboardButton(**kw)

# ───── ПОЛЬЗОВАТЕЛЬСКИЕ КЛАВИАТУРЫ ─────

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            _btn("Сдать сервис", "submit_service", callback_data="submit_service"),
            _btn("Профиль", "profile", callback_data="profile"),
        ],
        [_btn("Поддержка", "support", url=SUPPORT_LINK)],
    ])

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Вывод средств", "withdraw", callback_data="withdraw")],
        [_btn("Назад в меню", "back", callback_data="back_main")],
    ])

def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Отмена", "cancel", callback_data="cancel")]
    ])

def skip_photo_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Пропустить (без фото)", "skip_photo", callback_data="skip_photo")],
        [_btn("Отмена", "cancel", callback_data="cancel")],
    ])

def services_kb(ops: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for op in ops:
        btn_kwargs = {
            "text": f"{op['name']} — {op['price']}$",
            "callback_data": f"service_{op['id']}",
        }
        emoji_id = OPERATOR_EMOJIS.get(op.get("code")) or op.get("custom_emoji_id")
        if emoji_id:
            btn_kwargs["icon_custom_emoji_id"] = str(emoji_id)
        buttons.append([InlineKeyboardButton(**btn_kwargs)])
    buttons.append([_btn("Отмена", "cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться на канал", url=REQUIRED_CHANNEL_LINK)],
        [_btn("Проверить подписку", "check", callback_data="check_sub")],
    ])

def user_cancel_code_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("Отменить ввод кода", "cancel", callback_data=f"cancel_code_{req_id}")
    ]])

# ───── АДМИНИСТРАТИВНЫЕ КЛАВИАТУРЫ ─────

def admin_panel_kb(is_open: bool, is_auto: bool) -> InlineKeyboardMarkup:
    status_text = "Приостановить приём" if is_open else "Возобновить приём"
    status_cd   = "toggle_service_off" if is_open else "toggle_service_on"
    auto_text   = "Выключить авто-режим" if is_auto else "Включить авто (07:00–23:00 МСК)"
    auto_cd     = "auto_off" if is_auto else "auto_on"

    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Очередь заявок", "list", callback_data="admin_queue")],
        [_btn("Операторы", "operators", callback_data="admin_operators")],
        [_btn("Пополнить баланс", "balance", callback_data="admin_add_balance")],
        [_btn("Заявки на вывод", "withdraw", callback_data="admin_withdrawals")],
        [_btn("Пользователи", "users", callback_data="admin_users")],
        [_btn("Рассылка", "broadcast", callback_data="admin_broadcast")],
        [_btn(status_text, "warn" if is_open else "check", callback_data=status_cd)],
        [_btn(auto_text, "clock", callback_data=auto_cd)],
    ])

def admin_new_request_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Взять в работу", "take", callback_data=f"take_{req_id}")],
        [
            _btn("Отклонить заявку", "cancel", callback_data=f"reject_{req_id}"),
            _btn("Бан клиента", "cancel", callback_data=f"admin_ban_req_{req_id}")
        ],
        [_btn("Очередь", "back", callback_data="admin_queue")],
    ])

def admin_in_work_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Запросить код", "code", callback_data=f"req_code_{req_id}")],
        [_btn("Регион не подходит", "warn", callback_data=f"wrong_region_{req_id}")],
        [
            _btn("Завершить", "done", callback_data=f"done_{req_id}"),
            _btn("Отклонить", "cancel", callback_data=f"reject_{req_id}"),
        ],
        [_btn("Бан клиента", "cancel", callback_data=f"admin_ban_req_{req_id}")],
        [_btn("Назад в очередь", "back", callback_data="admin_queue")],
    ])

def admin_waiting_code_kb(req_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Запросить ещё код", "code", callback_data=f"req_code_{req_id}")],
        [_btn("Регион не подходит", "warn", callback_data=f"wrong_region_{req_id}")],
        [
            _btn("Завершить", "done", callback_data=f"done_{req_id}"),
            _btn("Отклонить", "cancel", callback_data=f"reject_{req_id}"),
        ],
        [_btn("Бан клиента", "cancel", callback_data=f"admin_ban_req_{req_id}")],
        [_btn("Назад в очередь", "back", callback_data="admin_queue")],
    ])

def reply_to_admin_kb(admin_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("Ответить", "pen", callback_data=f"reply_admin_{admin_id}")
    ]])

def reply_to_user_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("Ответить", "pen", callback_data=f"msg_user_{user_id}")
    ]])

def admin_operators_kb(ops: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for op in ops:
        status = "ON" if op["is_active"] else "OFF"
        btn_kwargs = {
            "text": f"[{status}] {op['name']} — {op['price']}$",
            "callback_data": f"admin_op_{op['id']}",
        }
        eid = OPERATOR_EMOJIS.get(op.get("code")) or op.get("custom_emoji_id")
        if eid:
            btn_kwargs["icon_custom_emoji_id"] = str(eid)
        buttons.append([InlineKeyboardButton(**btn_kwargs)])

    buttons.append([_btn("Добавить оператора", "add", callback_data="admin_op_add")])
    buttons.append([_btn("Назад в панель", "back", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_op_detail_kb(op: dict, ops: list[dict]) -> InlineKeyboardMarkup:
    op_id       = op["id"]
    toggle_text = "Выключить" if op["is_active"] else "Включить"
    toggle_cd   = f"admin_op_toggle_{op_id}"

    idx = next((i for i, o in enumerate(ops) if o["id"] == op_id), None)
    row_move = []
    if idx is not None and idx > 0:
        row_move.append(_btn("Выше", "back", callback_data=f"admin_op_up_{op_id}"))
    if idx is not None and idx < len(ops) - 1:
        row_move.append(_btn("Ниже", "send", callback_data=f"admin_op_down_{op_id}"))

    rows = [
        [_btn("Редактировать", "edit", callback_data=f"admin_op_edit_{op_id}")],
        [_btn("Настроить эмодзи", "photo", callback_data=f"admin_op_emoji_{op_id}")],
        [_btn(toggle_text, "warn" if op["is_active"] else "check", callback_data=toggle_cd)],
    ]
    if row_move:
        rows.append(row_move)
    rows.append([_btn("Удалить оператора", "delete", callback_data=f"admin_op_delete_{op_id}")])
    rows.append([_btn("Назад к списку", "back", callback_data="admin_operators")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_op_edit_fields_kb(op_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("Название", "pen", callback_data=f"admin_op_edit_name_{op_id}")],
        [_btn("Цена", "balance", callback_data=f"admin_op_edit_price_{op_id}")],
        [_btn("Вознаграждение", "gift", callback_data=f"admin_op_edit_reward_{op_id}")],
        [_btn("Назад", "back", callback_data=f"admin_op_{op_id}")],
    ])

def admin_withdrawals_kb(pending: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for r in pending:
        buttons.append([
            _btn(f"Выплатить #{r['id']} ({r['amount']}$)", "balance", callback_data=f"admin_pay_{r['id']}")
        ])
    buttons.append([_btn("Назад в панель", "back", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_broadcast_preview_kb(user_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(f"Отправить ({user_count} чел.)", "send", callback_data="broadcast_confirm")],
        [_btn("Изменить текст", "pen", callback_data="broadcast_edit")],
        [_btn("Отмена", "cancel", callback_data="cancel")],
    ])

def admin_users_kb(users: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append([_btn("Управление по ID", "pen", callback_data="admin_user_manage_by_id")])
    for u in users[:10]:
        uid = u["user_id"]
        uname = f"@{u['username']}" if u.get("username") else str(uid)
        status_flag = "⛔" if u.get("is_banned") else "👤"
        buttons.append([InlineKeyboardButton(
            text=f"{status_flag} {uname} ({uid})",
            callback_data=f"admin_user_card_{uid}"
        )])
    buttons.append([_btn("Назад в панель", "back", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_card_kb(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_btn_text = "Разблокировать" if is_banned else "Заблокировать"
    ban_btn_emoji = "check" if is_banned else "cancel"
    ban_cd = f"admin_unban_{user_id}" if is_banned else f"admin_ban_{user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            _btn(ban_btn_text, ban_btn_emoji, callback_data=ban_cd),
            _btn("Пополнить баланс", "balance", callback_data=f"admin_add_balance_{user_id}")
        ],
        [_btn("Написать пользователю", "pen", callback_data=f"msg_user_{user_id}")],
        [_btn("Назад к пользователям", "back", callback_data="admin_users")]
    ])
