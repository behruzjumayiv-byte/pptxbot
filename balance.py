import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class BalanceManager:
    """Foydalanuvchilar balansi bilan ishlash"""

    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(e)
            return {}
    
    def _save_users(self):
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(e)

    def ensure_user_exists(self, user_id: int):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "balance": 0,
                "total_slides": 0,
                "total_spent": 0
            }
            self._save_users()

    def get_user_info(self, user_id: int) -> Dict:
        self.ensure_user_exists(user_id)
        return self.users[str(user_id)]

    def add_balance(self, user_id: int, amount: int):
        user_id = str(user_id)
        self.ensure_user_exists(user_id)
        self.users[user_id]["balance"] += amount
        self._save_users()

    def deduct_balance(self, user_id: int, amount: int, slides: int):
        user_id = str(user_id)
        self.ensure_user_exists(user_id)
        self.users[user_id]["balance"] -= amount
        self.users[user_id]["total_slides"] += slides
        self.users[user_id]["total_spent"] += amount
        self._save_users()


balance_manager = BalanceManager()
