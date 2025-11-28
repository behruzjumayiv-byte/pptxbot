import os
print("USERS.JSON PATH =", os.path.abspath("users.json"))
print("CURRENT DIR =", os.getcwd())
print("FILES IN DIR =", os.listdir())
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from balance import BalanceManager
from ai import AIGenerator
from ppt_maker import PPTMaker
from utils import get_template_preview
import os

logger = logging.getLogger(__name__)

# FSM uchun States
class PresentationStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_author = State()
    waiting_for_slides_count = State()
    waiting_for_template = State()
    waiting_for_confirmation = State()

# Router yaratish
router = Router()
balance_manager = BalanceManager()
ai_generator = AIGenerator()
ppt_maker = PPTMaker()

def register_handlers(dp):
    """Barcha handlerlarni ro'yxatdan o'tkazish"""
    dp.include_router(router)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    import os
    print("BALANCE DB PATH =", os.getcwd(), " | FILES =", os.listdir())

    try:
        user_id = message.from_user.id
        balance_manager.ensure_user_exists(user_id)
        
        user_info = balance_manager.get_user_info(user_id)
        
        welcome_text = (
            f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n"
            f"🎯 Men sizga professional prezentatsiyalar tayyorlayman.\n\n"
            f"💰 Sizning balansingiz: {user_info['balance']:,} so'm\n"
            f"📊 Tayyorlangan slaydlar: {user_info['total_slides']}\n\n"
            f"📝 Prezentatsiya yaratish uchun quyidagilarni yuboring:\n"
            f"1️⃣ Mavzu nomini kiriting"
        )
        
        await message.answer(welcome_text)
        await state.set_state(PresentationStates.waiting_for_topic)
        
    except Exception as e:
        logger.error(f"Start komandasi xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Balansni ko'rsatish"""
    try:
        user_id = message.from_user.id
        user_info = balance_manager.get_user_info(user_id)
        
        text = (
            f"💰 Sizning balansingiz\n\n"
            f"💵 Joriy balans: {user_info['balance']:,} so'm\n"
            f"📊 Tayyorlangan slaydlar: {user_info['total_slides']}\n"
            f"💸 Jami sarflangan: {user_info['total_spent']:,} so'm\n\n"
            f"ℹ️ Har bir slayd: 500 so'm"
        )
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Balance komandasi xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Jarayonni bekor qilish"""
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi. /start orqali qaytadan boshlang.")

@router.message(PresentationStates.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    """Mavzu nomini olish"""
    try:
        topic = message.text.strip()
        
        if len(topic) < 3:
            await message.answer("❌ Mavzu nomi juda qisqa. Iltimos to'liqroq kiriting.")
            return
        
        await state.update_data(topic=topic)
        await message.answer(
            f"✅ Mavzu: {topic}\n\n"
            f"👤 Endi muallif ismini kiriting:"
        )
        await state.set_state(PresentationStates.waiting_for_author)
        
    except Exception as e:
        logger.error(f"Mavzu olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(PresentationStates.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    """Muallif nomini olish"""
    try:
        author = message.text.strip()
        
        if len(author) < 2:
            await message.answer("❌ Muallif nomi juda qisqa.")
            return
        
        await state.update_data(author=author)
        await message.answer(
            f"✅ Muallif: {author}\n\n"
            f"🔢 Slaydlar sonini kiriting (6-30 oralig'ida):"
        )
        await state.set_state(PresentationStates.waiting_for_slides_count)
        
    except Exception as e:
        logger.error(f"Muallif olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(PresentationStates.waiting_for_slides_count)
async def process_slides_count(message: Message, state: FSMContext):
    """Slaydlar sonini olish"""
    try:
        try:
            slides_count = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Iltimos faqat raqam kiriting.")
            return
        
        if slides_count < 6 or slides_count > 30:
            await message.answer("❌ Slaydlar soni 6 dan 30 gacha bo'lishi kerak.")
            return
        
        # Balansni tekshirish
        user_id = message.from_user.id
        cost = slides_count * 500
        user_info = balance_manager.get_user_info(user_id)
        
        if user_info['balance'] < cost:
            await message.answer(
                f"❌ Balansingiz yetarli emas!\n\n"
                f"💰 Kerakli summa: {cost:,} so'm\n"
                f"💵 Sizning balansingiz: {user_info['balance']:,} so'm\n"
                f"📉 Yetishmayotgan: {cost - user_info['balance']:,} so'm\n\n"
                f"👨‍💼 Balansni to'ldirish uchun adminga murojaat qiling: @admin"
            )
            await state.clear()
            return
        
        await state.update_data(slides_count=slides_count, cost=cost)
        
        # Shablonlarni ko'rsatish
        await message.answer("📸 Shablon tanlang:")
        
        # Shablonlarni yuborish
        buttons = []
        for i in range(1, 11):
            template_path = f"templates/{i}.png"
            if os.path.exists(template_path):
                try:
                    photo = FSInputFile(template_path)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"✅ {i}-shablon", callback_data=f"template_{i}")]
                    ])
                    await message.answer_photo(photo=photo, caption=f"Shablon {i}", reply_markup=keyboard)
                except Exception as e:
                    logger.error(f"Shablon {i} yuborishda xatolik: {e}")
        
        await state.set_state(PresentationStates.waiting_for_template)
        
    except Exception as e:
        logger.error(f"Slaydlar soni olishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.callback_query(F.data.startswith("template_"))
async def process_template_selection(callback: CallbackQuery, state: FSMContext):
    """Shablon tanlash"""
    try:
        template_num = callback.data.split("_")[1]
        await state.update_data(template=template_num)
        
        # Ma'lumotlarni olish
        data = await state.get_data()
        
        # Tasdiqlash uchun xabar
        confirmation_text = (
            f"📋 Ma'lumotlarni tasdiqlang:\n\n"
            f"📝 Mavzu: {data['topic']}\n"
            f"👤 Muallif: {data['author']}\n"
            f"🔢 Slaydlar soni: {data['slides_count']}\n"
            f"🎨 Shablon: {template_num}\n"
            f"💰 Narx: {data['cost']:,} so'm\n\n"
            f"✅ Tasdiqlaysizmi?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_yes"),
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="confirm_no")
            ]
        ])
        
        await callback.message.answer(confirmation_text, reply_markup=keyboard)
        await callback.answer()
        await state.set_state(PresentationStates.waiting_for_confirmation)
        
    except Exception as e:
        logger.error(f"Shablon tanlashda xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi.")

@router.callback_query(F.data == "confirm_no")
async def process_cancel_confirmation(callback: CallbackQuery, state: FSMContext):
    """Tasdiqni bekor qilish"""
    await state.clear()
    await callback.message.answer("❌ Jarayon bekor qilindi. /start orqali qaytadan boshlang.")
    await callback.answer()

@router.callback_query(F.data == "confirm_yes")
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    """Tasdiqdan keyin prezentatsiya yaratish"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        data = await state.get_data()
        
        # Jarayon boshlandi
        status_msg = await callback.message.answer(
            f"⏳ Prezentatsiya tayyorlanmoqda...\n"
            f"📊 Taxminiy vaqt: {data['slides_count'] * 3} soniya\n\n"
            f"1️⃣ AI matn generatsiya qilmoqda..."
        )
        
        # AI orqali matn yaratish
        try:
            slides_content = await ai_generator.generate_presentation(
                data['topic'], 
                data['author'], 
                data['slides_count']
            )
            
            await status_msg.edit_text(
                f"⏳ Prezentatsiya tayyorlanmoqda...\n"
                f"📊 Taxminiy vaqt: {data['slides_count'] * 3} soniya\n\n"
                f"✅ AI matn generatsiya qildi\n"
                f"2️⃣ PPTX fayl yaratilmoqda..."
            )
            
        except Exception as e:
            logger.error(f"AI generatsiya xatolik: {e}")
            await status_msg.edit_text("❌ AI matn yaratishda xatolik yuz berdi.")
            await state.clear()
            return
        
        # PPTX yaratish
        try:
            output_file = await ppt_maker.create_presentation(
                data['topic'],
                data['author'],
                slides_content,
                int(data['template'])
            )
            
            await status_msg.edit_text(
                f"⏳ Prezentatsiya tayyorlanmoqda...\n\n"
                f"✅ AI matn generatsiya qildi\n"
                f"✅ PPTX fayl yaratildi\n"
                f"3️⃣ Fayl yuborilmoqda..."
            )
            
        except Exception as e:
            logger.error(f"PPTX yaratishda xatolik: {e}")
            await status_msg.edit_text("❌ Prezentatsiya yaratishda xatolik yuz berdi.")
            await state.clear()
            return
        
        # Balansdan yechish
        balance_manager.deduct_balance(user_id, data['cost'], data['slides_count'])
        
        # Faylni yuborish
        try:
            document = FSInputFile(output_file)
            await callback.message.answer_document(
                document=document,
                caption=f"✅ Prezentatsiya tayyor!\n\n💰 {data['cost']:,} so'm yechildi."
            )
            
            # Faylni o'chirish
            if os.path.exists(output_file):
                os.remove(output_file)
                
            await status_msg.delete()
            
        except Exception as e:
            logger.error(f"Fayl yuborishda xatolik: {e}")
            await status_msg.edit_text("❌ Faylni yuborishda xatolik yuz berdi.")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Tasdiqlashda xatolik: {e}")
        await callback.message.answer("❌ Xatolik yuz berdi.")
        await state.clear()
