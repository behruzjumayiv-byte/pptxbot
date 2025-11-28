import sqlite3
import logging
from typing import Dict

logger = logging.getLogger(__name__)

import os
DB_PATH = os.path.join("/data", "users.db")   # Fly.io Launch Mode'da shu fayl saqlanadi

class BalanceManager:
    def __init__(self):
        self._connect()
        self._create_table()

    def _connect(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def _create_table(self):
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                total_slides INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Jadval yaratishda xatolik: {e}")

    def ensure_user_exists(self, user_id: int):
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO users (user_id, balance, total_slides, total_spent) VALUES (?, 0, 0, 0)",
                (user_id,)
            )
            self.conn.commit()

    def get_user_info(self, user_id: int) -> Dict:
        self.ensure_user_exists(user_id)
        self.cursor.execute("SELECT balance, total_slides, total_spent FROM users WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        return {
            "balance": row[0],
            "total_slides": row[1],
            "total_spent": row[2],
        }

    def add_balance(self, user_id: int, amount: int) -> bool:
        try:
            self.ensure_user_exists(user_id)
            self.cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Balans qo'shishda xatolik: {e}")
            return False

    def deduct_balance(self, user_id: int, amount: int, slides_count: int) -> bool:
        self.ensure_user_exists(user_id)

        self.cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = self.cursor.fetchone()[0]

        if balance < amount:
            return False

        try:
            self.cursor.execute(
                "UPDATE users SET balance = balance - ?, total_slides = total_slides + ?, total_spent = total_spent + ? WHERE user_id = ?",
                (amount, slides_count, amount, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Balansdan yechishda xatolik: {e}")
            return False

    def remove_balance(self, user_id: int, amount: int) -> bool:
        try:
            self.ensure_user_exists(user_id)
            self.cursor.execute(
                "UPDATE users SET balance = MAX(balance - ?, 0) WHERE user_id = ?",
                (amount, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Balans olib tashlashda xatolik: {e}")
            return False

    def get_statistics(self) -> Dict:
        try:
            self.cursor.execute("SELECT COUNT(*), SUM(total_slides), SUM(total_spent) FROM users")
            row = self.cursor.fetchone()
            return {
                "total_users": row[0] or 0,
                "total_slides": row[1] or 0,
                "total_earned": row[2] or 0
            }
        except Exception as e:
            logger.error(f"Statistika olishda xatolik: {e}")
            return {
                "total_users": 0,
                "total_slides": 0,
                "total_earned": 0
            }

    def get_all_users(self) -> Dict:
        self.cursor.execute("SELECT * FROM users")
        rows = self.cursor.fetchall()
        return rows
