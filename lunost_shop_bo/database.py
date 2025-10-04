import aiosqlite

DB_NAME = 'shop_bot.db'

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT,
                product_price INTEGER,
                original_price INTEGER,
                promo_code TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'pending',
                photo_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                discount INTEGER,
                description TEXT,
                max_uses INTEGER DEFAULT 0,
                current_uses INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

async def add_user(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
            (user_id, username, first_name)
        )
        await db.commit()

async def create_order(user_id: int, product_name: str, product_price: int, payment_method: str, original_price: int = None, promo_code: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'INSERT INTO orders (user_id, product_name, product_price, original_price, promo_code, payment_method) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, product_name, product_price, original_price or product_price, promo_code, payment_method)
        )
        await db.commit()
        return cursor.lastrowid

async def update_order_photo(order_id: int, photo_file_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE orders SET photo_file_id = ? WHERE order_id = ?', (photo_file_id, order_id))
        await db.commit()

async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
        await db.commit()

async def get_order(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)) as cursor:
            return await cursor.fetchone()

async def add_promocode(code: str, discount: int, description: str, max_uses: int = 0):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute('INSERT INTO promocodes (code, discount, description, max_uses) VALUES (?, ?, ?, ?)',
                           (code.upper(), discount, description, max_uses))
            await db.commit()
            return True
        except:
            return False

async def get_promocode(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM promocodes WHERE code = ? AND is_active = 1', (code.upper(),)) as cursor:
            return await cursor.fetchone()

async def use_promocode(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE promocodes SET current_uses = current_uses + 1 WHERE code = ?', (code.upper(),))
        await db.commit()

async def delete_promocode(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM promocodes WHERE code = ?', (code.upper(),))
        await db.commit()

async def get_all_promocodes():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM promocodes ORDER BY created_at DESC') as cursor:
            return await cursor.fetchall()

async def toggle_promocode(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE promocodes SET is_active = NOT is_active WHERE code = ?', (code.upper(),))
        await db.commit()
