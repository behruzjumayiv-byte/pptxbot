import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from balance import BalanceManager
import os

logger = logging.getLogger(__name__)

# Admin ID ro'yxati (.env dan olish mumkin)
ADMINS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# FSM uchun States
class AdminStates(StatesGroup):
    waiting_for_add_balance_user = State()
    waiting_for_add_balance_amount = State()
    waiting_for_remove_balance_user = State()
    waiting_for_remove_balance_amount = State()
    waiting_for_userinfo_user = State()
    waiting_for_broadcast_message = State()

# Router
router = Router()
balance_manager = BalanceManager()

def register_admin_handlers(dp):
    """Admin handlerlarni ro'yxatdan o'tkazish"""
    dp.include_router(router)

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMINS

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Balans qo'shish", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="➖ Balans ayirish", callback_data="admin_remove_balance")],
        [InlineKeyboardButton(text="👤 Foydalanuvchi ma'lumotlari", callback_data="admin_userinfo")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")]
    ])
    
    await message.answer(
        "🔐 <b>Admin Panel</b>\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_add_balance")
async def admin_add_balance_start(callback: CallbackQuery, state: FSMContext):
    """Balans qo'shish - user ID so'rash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q")
        return
    
    await callback.message.answer(
        "➕ <b>Balans qo'shish</b>\n\n"
        "Foydalanuvchi ID sini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_add_balance_user)
    await callback.answer()

@router.message(AdminStates.waiting_for_add_balance_user)
async def admin_add_balance_user(message: Message, state: FSMContext):
    """Balans qo'shish - user ID qabul qilish"""
    try:
        user_id = int(message.text.strip())
        await state.update_data(target_user_id=user_id)
        await message.answer(
            f"Foydalanuvchi ID: {user_id}\n\n"
            "Qo'shiladigan summani kiriting (so'mda):"
        )
        await state.set_state(AdminStates.waiting_for_add_balance_amount)
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam kiriting.")

@router.message(AdminStates.waiting_for_add_balance_amount)
async def admin_add_balance_amount(message: Message, state: FSMContext):
    """Balans qo'shish - summa qabul qilish"""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("❌ Summa musbat bo'lishi kerak.")
            return
        
        data = await state.get_data()
        user_id = data['target_user_id']
        
        success = balance_manager.add_balance(user_id, amount)
        
        if success:
            user_info = balance_manager.get_user_info(user_id)
            await message.answer(
                f"✅ Muvaffaqiyatli!\n\n"
                f"👤 User ID: {user_id}\n"
                f"➕ Qo'shildi: {amount:,} so'm\n"
                f"💰 Yangi balans: {user_info['balance']:,} so'm"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi.")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam kiriting.")

@router.callback_query(F.data == "admin_remove_balance")
async def admin_remove_balance_start(callback: CallbackQuery, state: FSMContext):
    """Balans ayirish - user ID so'rash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q")
        return
    
    await callback.message.answer(
        "➖ <b>Balans ayirish</b>\n\n"
        "Foydalanuvchi ID sini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_remove_balance_user)
    await callback.answer()

@router.message(AdminStates.waiting_for_remove_balance_user)
async def admin_remove_balance_user(message: Message, state: FSMContext):
    """Balans ayirish - user ID qabul qilish"""
    try:
        user_id = int(message.text.strip())
        await state.update_data(target_user_id=user_id)
        await message.answer(
            f"Foydalanuvchi ID: {user_id}\n\n"
            "Ayiriladigan summani kiriting (so'mda):"
        )
        await state.set_state(AdminStates.waiting_for_remove_balance_amount)
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam kiriting.")

@router.message(AdminStates.waiting_for_remove_balance_amount)
async def admin_remove_balance_amount(message: Message, state: FSMContext):
    """Balans ayirish - summa qabul qilish"""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("❌ Summa musbat bo'lishi kerak.")
            return
        
        data = await state.get_data()
        user_id = data['target_user_id']
        
        success = balance_manager.remove_balance(user_id, amount)
        
        if success:
            user_info = balance_manager.get_user_info(user_id)
            await message.answer(
                f"✅ Muvaffaqiyatli!\n\n"
                f"👤 User ID: {user_id}\n"
                f"➖ Ayirildi: {amount:,} so'm\n"
                f"💰 Yangi balans: {user_info['balance']:,} so'm"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi.")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam kiriting.")

@router.callback_query(F.data == "admin_userinfo")
async def admin_userinfo_start(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchi ma'lumotlari - user ID so'rash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q")
        return
    
    await callback.message.answer(
        "👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        "Foydalanuvchi ID sini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_userinfo_user)
    await callback.answer()

@router.message(AdminStates.waiting_for_userinfo_user)
async def admin_userinfo_show(message: Message, state: FSMContext):
    """Foydalanuvchi ma'lumotlarini ko'rsatish"""
    try:
        user_id = int(message.text.strip())
        user_info = balance_manager.get_user_info(user_id)
        
        text = (
            f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"💰 Balans: {user_info['balance']:,} so'm\n"
            f"📊 Tayyorlangan slaydlar: {user_info['total_slides']}\n"
            f"💸 Jami sarflangan: {user_info['total_spent']:,} so'm"
        )
        
        await message.answer(text, parse_mode="HTML")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam kiriting.")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Umumiy statistika"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q")
        return
    
    stats = balance_manager.get_statistics()
    
    text = (
        f"📊 <b>Umumiy statistika</b>\n\n"
        f"👥 Foydalanuvchilar soni: {stats['total_users']}\n"
        f"📄 Tayyorlangan slaydlar: {stats['total_slides']}\n"
        f"💰 Jami ishlangan summa: {stats['total_earned']:,} so'm"
    )
    
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Broadcast xabar - matn so'rash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q")
        return
    
    await callback.message.answer(
        "📢 <b>Broadcast xabar</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    """Broadcast xabarni yuborish"""
    broadcast_text = message.text
    users = balance_manager.get_all_users()
    
    success_count = 0
    fail_count = 0
    
    status_msg = await message.answer(
        f"📤 Xabar yuborilmoqda...\n"
        f"Jami: {len(users)} foydalanuvchi"
    )
    
    for user_id_str in users.keys():
        try:
            user_id = int(user_id_str)
            await message.bot.send_message(user_id, broadcast_text)
            success_count += 1
        except Exception as e:
            logger.error(f"Broadcast xatolik ({user_id_str}): {e}")
            fail_count += 1
    
    await status_msg.edit_text(
        f"✅ <b>Broadcast yakunlandi</b>\n\n"
        f"📨 Muvaffaqiyatli: {success_count}\n"
        f"❌ Xatolik: {fail_count}",
        parse_mode="HTML"
    )
    
    await state.clear()

# Command-based admin funksiyalar (eski uslub)
@router.message(Command("add_balance"))
async def cmd_add_balance(message: Message):
    """Balans qo'shish komandasi: /add_balance user_id amount"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Format: /add_balance user_id amount")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            await message.answer("❌ Summa musbat bo'lishi kerak.")
            return
        
        success = balance_manager.add_balance(user_id, amount)
        
        if success:
            user_info = balance_manager.get_user_info(user_id)
            await message.answer(
                f"✅ Muvaffaqiyatli!\n"
                f"User: {user_id}\n"
                f"Qo'shildi: {amount:,} so'm\n"
                f"Yangi balans: {user_info['balance']:,} so'm"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi.")
            
    except (ValueError, IndexError):
        await message.answer("❌ Format: /add_balance user_id amount")

@router.message(Command("remove_balance"))
async def cmd_remove_balance(message: Message):
    """Balans ayirish komandasi: /remove_balance user_id amount"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Format: /remove_balance user_id amount")
            return
        
        user_id = int(parts[1])
        amount = int(parts[2])
        
        if amount <= 0:
            await message.answer("❌ Summa musbat bo'lishi kerak.")
            return
        
        success = balance_manager.remove_balance(user_id, amount)
        
        if success:
            user_info = balance_manager.get_user_info(user_id)
            await message.answer(
                f"✅ Muvaffaqiyatli!\n"
                f"User: {user_id}\n"
                f"Ayirildi: {amount:,} so'm\n"
                f"Yangi balans: {user_info['balance']:,} so'm"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi.")
            
    except (ValueError, IndexError):
        await message.answer("❌ Format: /remove_balance user_id amount")

@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    """Foydalanuvchi ma'lumotlari: /userinfo user_id"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("❌ Format: /userinfo user_id")
            return
        
        user_id = int(parts[1])
        user_info = balance_manager.get_user_info(user_id)
        
        text = (
            f"👤 Foydalanuvchi: {user_id}\n"
            f"💰 Balans: {user_info['balance']:,} so'm\n"
            f"📊 Slaydlar: {user_info['total_slides']}\n"
            f"💸 Sarflangan: {user_info['total_spent']:,} so'm"
        )
        
        await message.answer(text)
        
    except (ValueError, IndexError):
        await message.answer("❌ Format: /userinfo user_id")
