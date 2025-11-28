import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

import os

DB_PATH = "/root/pptxbot/users.json"

class BalanceManager:
    def __init__(self, users_file: str = DB_PATH):
        self.users_file = users_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Foydalanuvchilar ma'lumotlarini yuklash"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Foydalanuvchilarni yuklashda xatolik: {e}")
            return {}
    
    def _save_users(self):
        """Foydalanuvchilar ma'lumotlarini saqlash"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Foydalanuvchilarni saqlashda xatolik: {e}")
    
    def ensure_user_exists(self, user_id: int):
        """Foydalanuvchini ro'yxatga olish (agar mavjud bo'lmasa)"""
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "balance": 0,
                "total_slides": 0,
                "total_spent": 0
            }
            self._save_users()
            logger.info(f"Yangi foydalanuvchi qo'shildi: {user_id}")
    
    def get_user_info(self, user_id: int) -> Dict:
        """Foydalanuvchi ma'lumotlarini olish"""
        self.ensure_user_exists(user_id)
        return self.users[str(user_id)].copy()
    
    def add_balance(self, user_id: int, amount: int) -> bool:
        """Balansga pul qo'shish"""
        try:
            self.ensure_user_exists(user_id)
            user_id_str = str(user_id)
            self.users[user_id_str]["balance"] += amount
            self._save_users()
            logger.info(f"Foydalanuvchi {user_id} balansiga {amount} qo'shildi")
            return True
        except Exception as e:
            logger.error(f"Balans qo'shishda xatolik: {e}")
            return False
    
    def deduct_balance(self, user_id: int, amount: int, slides_count: int) -> bool:
        """Balansdan pul yechish"""
        try:
            self.ensure_user_exists(user_id)
            user_id_str = str(user_id)
            
            if self.users[user_id_str]["balance"] < amount:
                logger.warning(f"Foydalanuvchi {user_id} balansi yetarli emas")
                return False
            
            self.users[user_id_str]["balance"] -= amount
            self.users[user_id_str]["total_spent"] += amount
            self.users[user_id_str]["total_slides"] += slides_count
            self._save_users()
            logger.info(f"Foydalanuvchi {user_id} balansidan {amount} yechildi")
            return True
        except Exception as e:
            logger.error(f"Balans yechishda xatolik: {e}")
            return False
    
    def remove_balance(self, user_id: int, amount: int) -> bool:
        """Balansdan pul olib tashlash (admin uchun)"""
        try:
            self.ensure_user_exists(user_id)
            user_id_str = str(user_id)
            
            self.users[user_id_str]["balance"] = max(0, self.users[user_id_str]["balance"] - amount)
            self._save_users()
            logger.info(f"Foydalanuvchi {user_id} balansidan {amount} olib tashlandi")
            return True
        except Exception as e:
            logger.error(f"Balans olib tashlashda xatolik: {e}")
            return False
    
    def get_all_users(self) -> Dict:
        """Barcha foydalanuvchilarni olish"""
        return self.users.copy()
    
    def get_statistics(self) -> Dict:
        """Umumiy statistika"""
        try:
            total_users = len(self.users)
            total_slides = sum(user["total_slides"] for user in self.users.values())
            total_earned = sum(user["total_spent"] for user in self.users.values())
            
            return {
                "total_users": total_users,
                "total_slides": total_slides,
                "total_earned": total_earned
            }
        except Exception as e:
            logger.error(f"Statistika olishda xatolik: {e}")
            return {
                "total_users": 0,
                "total_slides": 0,
                "total_earned": 0
            }
