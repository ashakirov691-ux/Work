import sqlite3
import logging
import re
from contextlib import contextmanager
from config import DB_PATH

def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db():
    conn = db_connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Инициализация таблиц базы данных и выполнение миграций."""
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT    DEFAULT '',
            full_name   TEXT    DEFAULT '',
            balance     REAL    DEFAULT 0.0,
            completed   INTEGER DEFAULT 0,
            cancelled   INTEGER DEFAULT 0,
            in_work     INTEGER DEFAULT 0,
            paid        REAL    DEFAULT 0.0,
            is_banned   INTEGER DEFAULT 0,
            ban_reason  TEXT    DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS operators (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            code            TEXT    UNIQUE NOT NULL,
            name            TEXT    NOT NULL,
            price           REAL    NOT NULL,
            reward_amount   REAL    NOT NULL DEFAULT 0.0,
            custom_emoji_id TEXT,
            is_active       INTEGER DEFAULT 1,
            sort_order      INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS service_requests (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            username         TEXT    DEFAULT '',
            operator_id      INTEGER NOT NULL,
            service_name     TEXT    NOT NULL,
            price            REAL    NOT NULL,
            reward_amount    REAL    NOT NULL DEFAULT 0.0,
            phone            TEXT    NOT NULL,
            photo_file_id    TEXT,
            status           TEXT    DEFAULT 'queue',
            admin_id         INTEGER,
            admin_msg_id     INTEGER,
            code_count       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            username  TEXT    DEFAULT '',
            amount    REAL    NOT NULL,
            status    TEXT    DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        conn.execute("INSERT OR IGNORE INTO settings VALUES ('service_open','1')")
        conn.execute("INSERT OR IGNORE INTO settings VALUES ('auto_mode','1')")

        # Миграции для users
        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "is_banned" not in user_cols:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
                logging.info("Миграция: добавлена колонка users.is_banned")
            except Exception as e:
                logging.warning("Миграция users.is_banned: %s", e)
        if "ban_reason" not in user_cols:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT DEFAULT ''")
                logging.info("Миграция: добавлена колонка users.ban_reason")
            except Exception as e:
                logging.warning("Миграция users.ban_reason: %s", e)

        # Миграции для service_requests
        cols = {r[1] for r in conn.execute("PRAGMA table_info(service_requests)").fetchall()}
        migrations = {
            "operator_id":   "INTEGER DEFAULT 0",
            "reward_amount": "REAL DEFAULT 0.0",
            "code_count":    "INTEGER DEFAULT 0",
            "admin_id":      "INTEGER",
            "admin_msg_id":  "INTEGER",
            "photo_file_id": "TEXT",
            "service_name":  "TEXT DEFAULT ''",
            "price":         "REAL DEFAULT 0.0",
            "phone":         "TEXT DEFAULT ''",
            "status":        "TEXT DEFAULT 'queue'",
            "username":      "TEXT DEFAULT ''",
            "service_key":   "TEXT DEFAULT ''",
        }
        for col, typedef in migrations.items():
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE service_requests ADD COLUMN {col} {typedef}")
                    logging.info("Миграция: добавлена колонка service_requests.%s", col)
                except Exception as e:
                    logging.warning("Миграция %s: %s", col, e)

        if "service_key" in {r[1] for r in conn.execute("PRAGMA table_info(service_requests)").fetchall()}:
            try:
                conn.execute("UPDATE service_requests SET service_key='' WHERE service_key IS NULL")
            except Exception:
                pass

        # Миграции для operators
        op_cols = {r[1] for r in conn.execute("PRAGMA table_info(operators)").fetchall()}
        op_migrations = {
            "reward_amount":   "REAL DEFAULT 0.0",
            "custom_emoji_id": "TEXT",
            "is_active":       "INTEGER DEFAULT 1",
            "sort_order":      "INTEGER DEFAULT 0",
            "created_at":      "TEXT DEFAULT (datetime('now'))",
        }
        for col, typedef in op_migrations.items():
            if col not in op_cols:
                try:
                    conn.execute(f"ALTER TABLE operators ADD COLUMN {col} {typedef}")
                    logging.info("Миграция: добавлена колонка operators.%s", col)
                except Exception as e:
                    logging.warning("Миграция operators.%s: %s", col, e)

        defaults = [
            ("sbermobile", "Сбермобайл", 17.0, 17.0, 1),
            ("mts",        "МТС",        12.0, 12.0, 2),
            ("megafon",    "МегаФон",    13.0, 13.0, 3),
            ("beeline",    "Билайн",     18.0, 18.0, 4),
            ("tmobile",    "Т-Мобайл",  16.0, 16.0, 5),
            ("maxnereg",   "Макс нерег", 5.0,  5.0,  6),
            ("tg",         "TG",         10.0, 10.0, 7),
            ("telegram",   "Telegram",   10.0, 10.0, 8),
        ]
        for code, name, price, reward, sort in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO operators (code,name,price,reward_amount,sort_order) VALUES (?,?,?,?,?)",
                (code, name, price, reward, sort)
            )

# ───── USERS ─────
def get_user(user_id: int) -> dict:
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            return {
                "user_id": user_id, "username": "", "full_name": "",
                "balance": 0.0, "completed": 0, "cancelled": 0, "in_work": 0, "paid": 0.0,
                "is_banned": 0, "ban_reason": ""
            }
        return dict(row)

def update_user(user_id: int, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with db() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE user_id=?", (*kwargs.values(), user_id))

def upsert_user(user_id: int, username: str, full_name: str):
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, full_name) VALUES (?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
        """, (user_id, username, full_name))

def get_all_user_ids() -> list[int]:
    with db() as conn:
        return [r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]

def get_all_users(limit=100) -> list[dict]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY user_id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def is_user_banned(user_id: int) -> bool:
    with db() as conn:
        row = conn.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,)).fetchone()
        return bool(row["is_banned"]) if row else False

def ban_user(user_id: int, reason: str = ""):
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, is_banned, ban_reason) VALUES (?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET is_banned=1, ban_reason=excluded.ban_reason
        """, (user_id, reason))

def unban_user(user_id: int):
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, is_banned, ban_reason) VALUES (?, 0, '')
            ON CONFLICT(user_id) DO UPDATE SET is_banned=0, ban_reason=''
        """, (user_id,))

# ───── OPERATORS ─────
def get_operators(active_only=False) -> list[dict]:
    with db() as conn:
        q = "SELECT * FROM operators"
        if active_only:
            q += " WHERE is_active=1"
        q += " ORDER BY sort_order ASC, id ASC"
        return [dict(r) for r in conn.execute(q).fetchall()]

def get_operator(op_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM operators WHERE id=?", (op_id,)).fetchone()
        return dict(row) if row else None

def get_operator_by_code(code: str) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM operators WHERE code=?", (code,)).fetchone()
        return dict(row) if row else None

def create_operator(code: str, name: str, price: float, reward: float, sort_order: int = None) -> int:
    with db() as conn:
        if sort_order is None:
            row = conn.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM operators").fetchone()
            sort_order = row[0]
        cur = conn.execute(
            "INSERT INTO operators (code,name,price,reward_amount,sort_order) VALUES (?,?,?,?,?)",
            (code, name, price, reward, sort_order)
        )
        return cur.lastrowid

def update_operator(op_id: int, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with db() as conn:
        conn.execute(f"UPDATE operators SET {sets} WHERE id=?", (*kwargs.values(), op_id))

def delete_operator(op_id: int):
    with db() as conn:
        conn.execute("DELETE FROM operators WHERE id=?", (op_id,))

def swap_operator_sort(op_id: int, direction: str):
    """Поднять (up) или опустить (down) оператора в списке."""
    with db() as conn:
        cur = conn.execute("SELECT sort_order FROM operators WHERE id=?", (op_id,)).fetchone()
        if not cur: return
        cur_sort = cur[0]
        if direction == "up":
            neighbor = conn.execute(
                "SELECT id, sort_order FROM operators WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1",
                (cur_sort,)
            ).fetchone()
        else:
            neighbor = conn.execute(
                "SELECT id, sort_order FROM operators WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1",
                (cur_sort,)
            ).fetchone()
        if not neighbor: return
        n_id, n_sort = neighbor["id"], neighbor["sort_order"]
        conn.execute("UPDATE operators SET sort_order=? WHERE id=?", (n_sort, op_id))
        conn.execute("UPDATE operators SET sort_order=? WHERE id=?", (cur_sort, n_id))

# ───── REQUESTS ─────
def create_service_request(user_id: int, username: str, operator_id: int, service_name: str,
                           price: float, reward: float, phone: str, photo_file_id: str | None) -> int:
    with db() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(service_requests)").fetchall()}
        service_key = ""
        if operator_id:
            op = conn.execute("SELECT code FROM operators WHERE id=?", (operator_id,)).fetchone()
            if op:
                service_key = op[0] or ""
        if not service_key and service_name:
            service_key = service_name

        fields = ["user_id", "username", "service_name", "price", "phone"]
        values = [user_id, username, service_name, price, phone]

        if "operator_id" in cols:
            fields.append("operator_id")
            values.append(operator_id)
        if "reward_amount" in cols:
            fields.append("reward_amount")
            values.append(reward)
        if "photo_file_id" in cols:
            fields.append("photo_file_id")
            values.append(photo_file_id)
        if "service_key" in cols:
            fields.append("service_key")
            values.append(service_key)
        if "status" in cols:
            fields.append("status")
            values.append("queue")
        if "code_count" in cols:
            fields.append("code_count")
            values.append(0)

        placeholders = ",".join("?" * len(fields))
        field_list = ",".join(fields)
        cur = conn.execute(
            f"INSERT INTO service_requests ({field_list}) VALUES ({placeholders})",
            values
        )
        return cur.lastrowid

def get_request(req_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM service_requests WHERE id=?", (req_id,)).fetchone()
        return dict(row) if row else None

def update_request(req_id: int, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with db() as conn:
        conn.execute(f"UPDATE service_requests SET {sets} WHERE id=?", (*kwargs.values(), req_id))

def get_active_requests() -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM service_requests WHERE status IN ('queue','in_work','waiting_code') ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]

def get_user_active_request(user_id: int) -> dict | None:
    """Возвращает последнюю активную заявку пользователя (в очереди, в работе, ожидает код)."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM service_requests WHERE user_id=? AND status IN ('queue','in_work','waiting_code') ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

def normalize_phone(phone: str) -> str:
    """Очищает телефон до цифр. Для РФ номеров приводит 11-значные к 10 цифрам без первой 7/8."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith(("7", "8")):
        return digits[1:]
    return digits

def is_phone_already_submitted(phone: str) -> tuple[bool, str]:
    """Проверяет, находится ли номер в заявке или был сдан ранее.
    Возвращает (is_taken, reason)."""
    norm = normalize_phone(phone)
    if not norm or len(norm) < 6:
        return False, ""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, phone, status, service_name FROM service_requests WHERE status IN ('queue','in_work','waiting_code','done')"
        ).fetchall()
        for r in rows:
            if normalize_phone(r["phone"]) == norm:
                if r["status"] in ("queue", "in_work", "waiting_code"):
                    return True, f"Номер <code>{phone}</code> уже находится в заявке #{r['id']} ({r['service_name']})."
                elif r["status"] == "done":
                    return True, f"Номер <code>{phone}</code> уже был успешно сдан ранее (Заявка #{r['id']})."
    return False, ""

# ───── WITHDRAWALS ─────
def create_withdrawal(user_id: int, username: str, amount: float) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO withdrawal_requests (user_id, username, amount) VALUES (?,?,?)",
            (user_id, username, amount)
        )
        return cur.lastrowid

def get_user_pending_withdrawal(user_id: int) -> dict | None:
    """Возвращает активную заявку на вывод пользователя со статусом 'pending'."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM withdrawal_requests WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

def get_pending_withdrawals() -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM withdrawal_requests WHERE status='pending' ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]

def get_withdrawal(wid: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM withdrawal_requests WHERE id=?", (wid,)).fetchone()
        return dict(row) if row else None

def update_withdrawal(wid: int, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    with db() as conn:
        conn.execute(f"UPDATE withdrawal_requests SET {sets} WHERE id=?", (*kwargs.values(), wid))

# ───── SETTINGS ─────
def get_setting(key: str, default: str = "") -> str:
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )

def is_service_open() -> bool:
    return get_setting("service_open", "1") == "1"

def is_auto_mode() -> bool:
    return get_setting("auto_mode", "1") == "1"
