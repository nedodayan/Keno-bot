import aiosqlite

DB_PATH = "keno.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 50.0,
                total_deposited REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0,
                games_played INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT, -- 'deposit' or 'withdrawal'
                amount REAL,
                status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                reference_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                bet_amount REAL,
                spots_count INTEGER,
                selected_numbers TEXT,
                drawn_numbers TEXT,
                matched_count INTEGER,
                payout REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_user(user_id: int, username: str, bonus: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)",
            (user_id, username, bonus)
        )
        await db.commit()

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def set_balance(user_id: int, new_balance: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        await db.commit()

async def record_game(user_id: int, bet: float, spots: int, selected: list, drawn: list, matches: int, payout: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO games (user_id, bet_amount, spots_count, selected_numbers, drawn_numbers, matched_count, payout)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, bet, spots, ",".join(map(str, selected)), ",".join(map(str, drawn)), matches, payout))
        await db.execute("UPDATE users SET games_played = games_played + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_recent_games(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM games WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ) as cursor:
            return await cursor.fetchall()

async def get_leaderboard(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT username, balance, games_played FROM users ORDER BY balance DESC LIMIT ?", (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def create_transaction(user_id: int, tx_type: str, amount: float, reference_info: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO transactions (user_id, type, amount, reference_info)
            VALUES (?, ?, ?, ?)
        """, (user_id, tx_type, amount, reference_info))
        await db.commit()
        return cursor.lastrowid

async def get_pending_transactions():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM transactions WHERE status = 'pending' ORDER BY id ASC"
        ) as cursor:
            return await cursor.fetchall()

async def update_transaction_status(tx_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE transactions SET status = ? WHERE id = ?", (status, tx_id))
        await db.commit()

async def get_global_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT 
                COUNT(*) as total_users,
                COALESCE(SUM(balance), 0) as total_balance,
                COALESCE(SUM(total_deposited), 0) as total_deposited,
                COALESCE(SUM(total_withdrawn), 0) as total_withdrawn,
                COALESCE(SUM(games_played), 0) as total_games
            FROM users
        """) as cursor:
            return await cursor.fetchone()
