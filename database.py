import psycopg2
from config import DB_CONFIG

class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            self.init_tables()
            print("Подключение к базе данных успешно!")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            raise

    def init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount DECIMAL(10, 2),
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        print("Таблицы созданы или уже существуют.")

    def register_user(self, user_id, username):
        self.cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
            (user_id, username)
        )
        self.conn.commit()
        print(f"Пользователь {username} зарегистрирован")

    def add_expense(self, user_id, amount, category):
        self.cursor.execute(
            "INSERT INTO expenses (user_id, amount, category) VALUES (%s, %s, %s)",
            (user_id, amount, category)
        )
        self.conn.commit()
        print(f"Расход {amount} в категории {category} добавлен")

    def get_report(self, user_id, period):
        if period == "month":
            query = """
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = %s
                AND created_at >= CURRENT_DATE - INTERVAL '1 month'
                GROUP BY category
            """
        elif period == "year":
            query = """
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = %s
                AND created_at >= CURRENT_DATE - INTERVAL '1 year'
                GROUP BY category
            """
        else:
            raise ValueError("Неподдерживаемый период")
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def get_top_category(self, user_id):
        query = """
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        """
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()

    def get_stats(self, user_id, period, category=None):
        query = """
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = %s
            AND created_at >= CURRENT_DATE - INTERVAL %s
        """
        params = [user_id, f"1 {period}"]
        if category:
            query += " AND category = %s"
            params.append(category)
        query += " GROUP BY category"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
        print("Соединение с базой данных закрыто.")