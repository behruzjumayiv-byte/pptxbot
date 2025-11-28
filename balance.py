import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# USER FILE DOIMIY JOYGA YOZILADI
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)
USER_FILE = os.path.join(DATA_DIR, "users.json")

class BalanceManager:
    def __init__(self):
        self.users_file = USER_FILE
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Foydalanuvchilarni yuklashda xatolik: {e}")
            return {}

    def _save_users(self):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Foydalanuvchilarni saqlashda xatolik: {e}")

    def ensure_user_exists(self, user_id: int):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {"balance": 0, "total_slides": 0, "total_spent": 0}
            self._save_users()

    def add_balance(self, user_id: int, amount: int) -> bool:
        try:
            self.ensure_user_exists(user_id)
            user_id = str(user_id)
            self.users[user_id]["balance"] += amount
            self._save_users()
            return True
        except:
            return False

    def deduct_balance(self, user_id: int, amount: int, slides_count: int) -> bool:
        try:
            self.ensure_user_exists(user_id)
            user_id = str(user_id)

            if self.users[user_id]["balance"] < amount:
                return False

            self.users[user_id]["balance"] -= amount
            self.users[user_id]["total_spent"] += amount
            self.users[user_id]["total_slides"] += slides_count
            self._save_users()
            return True
        except:
            return False

    def get_user_info(self, user_id: int) -> Dict:
        self.ensure_user_exists(user_id)
        return self.users[str(user_id)]
