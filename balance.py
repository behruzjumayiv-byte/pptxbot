import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class BalanceManager:
    """Foydalanuvchilar balansi bilan ishlash"""

    def __init__(self, users_file: str = "/data/users.json"):
        self.users_file = users_file
        self._ensure_storage()
        self.users = self._load_users()

    def _ensure_storage(self):
        """Fly.io uchun /data katalogini tekshirish"""
        os.makedirs("/data", exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_users(self) -> Dict:
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_users(self):
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Foydalanuvchilarni saqlashda xatolik: {e}")

    def ensure_user_exists(self, user_id: int):
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "balance": 0,
                "total_slides": 0,
                "total_spent": 0
            }
            self._save_users()

    def get_user_info(self, user_id: int) -> Dict:
        self.ensure_user_exists(user_id)
        return self.users[str(user_id)].copy()

    def add_balance(self, user_id: int, amount: int) -> bool:
        self.ensure_user_exists(user_id)
        user_id_str = str(user_id)
        self.users[user_id_str]["balance"] += amount
        self._save_users()
        return True

    def deduct_balance(self, user_id: int, amount: int, slides_count: int) -> bool:
        self.ensure_user_exists(user_id)
        user_id_str = str(user_id)

        if self.users[user_id_str]["balance"] < amount:
            return False

        self.users[user_id_str]["balance"] -= amount
        self.users[user_id_str]["total_spent"] += amount
        self.users[user_id_str]["total_slides"] += slides_count
        self._save_users()
        return True

    def remove_balance(self, user_id: int, amount: int) -> bool:
        self.ensure_user_exists(user_id)
        user_id_str = str(user_id)
        self.users[user_id_str]["balance"] = max(0, self.users[user_id_str]["balance"] - amount)
        self._save_users()
        return True

    def get_all_users(self) -> Dict:
        return self.users.copy()

    def get_statistics(self) -> Dict:
        total_users = len(self.users)
        total_slides = sum(u["total_slides"] for u in self.users.values())
        total_earned = sum(u["total_spent"] for u in self.users.values())

        return {
            "total_users": total_users,
            "total_slides": total_slides,
            "total_earned": total_earned
        }
