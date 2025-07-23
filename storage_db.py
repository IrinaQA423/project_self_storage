import sqlite3
from datetime import datetime


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        email TEXT,
        registration_date TIMESTAMP
    )
    ''')

    # Создаем таблицу складов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS warehouses (
        warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        description TEXT
    )
    ''')

    # Создаем таблицу боксов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS storage_boxes (
        box_id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER,
        size TEXT NOT NULL,
        price INTEGER NOT NULL,
        is_available BOOLEAN DEFAULT 1,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
    )
    ''')

    # Создаем таблицу заказов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        box_id INTEGER,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
        total_price INTEGER,
        status TEXT DEFAULT 'processing',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (box_id) REFERENCES storage_boxes(box_id)
    )
    ''')

    warehouses = [
        ("📍 г. Москва, ул. Ленина, д. 10", "Основной склад с боксами разных размеров"),
        ("📍 г. Москва, пр. Мира, д. 25", "Склад с климат-контролем"),
        ("📍 г. Москва, ул. Тверская, д. 15", "Центральный склад")
    ]
    cursor.executemany("INSERT INTO warehouses (address, description) VALUES (?, ?)", warehouses)

    # Добавляем типы боксов
    boxes = [
        (1, "Малый (3 м³)", 1500),
        (1, "Средний (5 м³)", 3500),
        (1, "Большой (10 м³)", 5000),
        (2, "Малый (3 м³)", 1700),
        (2, "Средний (5 м³)", 3700),
        (2, "Большой (10 м³)", 5200),
        (3, "Малый (3 м³)", 1600),
        (3, "Средний (5 м³)", 3600),
        (3, "Большой (10 м³)", 5100)
    ]
    cursor.executemany("INSERT INTO storage_boxes (warehouse_id, size, price) VALUES (?, ?, ?)", boxes)

    conn.commit()
    conn.close()


def save_user(user_data):
    """Сохранение данных пользователя"""
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO users
    (user_id, username, first_name, last_name, phone, email, registration_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data.get('user_id'),
        user_data.get('username'),
        user_data.get('first_name'),
        user_data.get('last_name'),
        user_data.get('phone'),
        user_data.get('email'),
        datetime.now()
    ))
    conn.commit()
    conn.close()


def save_order(order_data):
    """Сохранение заказа"""
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO orders
    (user_id, box_id, start_date, end_date, total_price)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        order_data.get('user_id'),
        order_data.get('box_id'),
        order_data.get('start_date'),
        order_data.get('end_date'),
        order_data.get('total_price')
    ))

    conn.commit()
    conn.close()
    return cursor.lastrowid


def get_warehouses():
    """Получение списка складов"""
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()

    conn.close()
    return warehouses


def get_available_boxes(warehouse_id):
    """Получение доступных боксов на складе"""
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM storage_boxes
    WHERE warehouse_id = ? AND is_available = 1
    ''', (warehouse_id,))

    boxes = cursor.fetchall()
    conn.close()
    return boxes


def show_database_content():
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()

    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("\nСодержимое базы данных:")
    for table in tables:
        table_name = table[0]
        print(f"\nТаблица: {table_name}")
        print("Структура:")

        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # Получаем содержимое таблицы
        print("\nДанные:")
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    conn.close()
