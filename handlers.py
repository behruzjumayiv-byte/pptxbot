import os
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from balance import balance_manager
from ai import AIGenerator
from ppt_maker import PPTMaker

logger = logging.getLogger(__name__)

# ================================
#  FSM STATES
# ================================
class PresentationStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_author = State()
    waiting_for_slides_count = State()
    waiting_for_template = State()
    waiting_for_confirmation = State()


router = Router()
ai_generator = AIGenerator()
ppt_maker = PPTMaker()


# ================================
#   DIZAYN TUGMA KLAVIATURASI
# ================================
def design_keyboard(current: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"design_prev_{current}"),
            InlineKeyboardButton(text=f"Dizayn {current}", callback_data=f"design_select_{current}"),
            InlineKeyboardButton(text="➡️", callback_data=f"design_next_{current}")
        ],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="design_back")]
    ])


# ================================
# /start – foydalanuvchini kutib olish
# ================================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        balance_manager.ensure_user_exists(user_id)
        data = balance_manager.get_user_info(user_id)

        text = (
            f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n"
            f"💰 Balans: {data['balance']:,} so'm\n"
            f"📊 Tayyorlangan slaydlar: {data['total_slides']}\n\n"
            f"1️⃣ Prezentatsiya mavzusini yuboring:"
        )

        await message.answer(text)
        await state.set_state(PresentationStates.waiting_for_topic)
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")


# ================================
#  Mavzu → Muallif
# ================================
@router.message(PresentationStates.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    if len(topic) < 3:
        return await message.answer("❌ Mavzu juda qisqa. Kamida 3 ta belgi kiriting.")

    await state.update_data(topic=topic)
    await message.answer("✅ Muallif ismini yuboring:")
    await state.set_state(PresentationStates.waiting_for_author)


# ================================
#  Muallif → Slaydlar soni
# ================================
@router.message(PresentationStates.waiting_for_author)
async def process_author(message: Message, state: FSMContext):
    author = message.text.strip()
    if len(author) < 2:
        return await message.answer("❌ Muallif ismi juda qisqa.")

    await state.update_data(author=author)
    await message.answer("📄 Slaydlar sonini yuboring (6–30):")
    await state.set_state(PresentationStates.waiting_for_slides_count)


# ================================
#  Slaydlar soni → DIZAYN TANLASH
# ================================
@router.message(PresentationStates.waiting_for_slides_count)
async def process_slides_count(message: Message, state: FSMContext):
    try:
        slides = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ Faqat raqam kiriting.")

    if slides < 6 or slides > 30:
        return await message.answer("❌ Slaydlar 6–30 oralig'ida bo'lishi kerak.")

    user_id = message.from_user.id
    cost = slides * 500
    info = balance_manager.get_user_info(user_id)

    if info["balance"] < cost:
        return await message.answer(
            f"❌ Balans yetarli emas!\n"
            f"Kerak: {cost:,} so'm\n"
            f"Sizda: {info['balance']:,} so'm"
        )

    await state.update_data(slides_count=slides, cost=cost)

    # 🔥 1-dizayn rasmi
    template_path = "templates/1.png"
    
    if not os.path.exists(template_path):
        return await message.answer("❌ Template fayl topilmadi. Administratorga murojaat qiling.")
    
    img = FSInputFile(template_path)

    await message.answer_photo(
        photo=img,
        caption="🎨 Marhamat, dizayn tanlang:",
        reply_markup=design_keyboard(1)
    )

    await state.set_state(PresentationStates.waiting_for_template)


# ================================
#  DIZAYN ← oldingi
# ================================
@router.callback_query(F.data.startswith("design_prev_"))
async def prev_design(call: CallbackQuery, state: FSMContext):
    try:
        cur = int(call.data.split("_")[-1])
        new = 10 if cur == 1 else cur - 1

        template_path = f"templates/{new}.png"
        
        if not os.path.exists(template_path):
            await call.answer("❌ Template topilmadi!", show_alert=True)
            return
        
        img = FSInputFile(template_path)

        await call.message.edit_media(
            media=InputMediaPhoto(media=img),
            reply_markup=design_keyboard(new)
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Error in prev_design: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)


# ================================
#  DIZAYN → keyingi
# ================================
@router.callback_query(F.data.startswith("design_next_"))
async def next_design(call: CallbackQuery, state: FSMContext):
    try:
        cur = int(call.data.split("_")[-1])
        new = 1 if cur == 10 else cur + 1

        template_path = f"templates/{new}.png"
        
        if not os.path.exists(template_path):
            await call.answer("❌ Template topilmadi!", show_alert=True)
            return
        
        img = FSInputFile(template_path)

        await call.message.edit_media(
            media=InputMediaPhoto(media=img),
            reply_markup=design_keyboard(new)
        )
        await call.answer()
    except Exception as e:
        logger.error(f"Error in next_design: {e}")
        await call.answer("❌ Xatolik yuz berdi", show_alert=True)


# ================================
#  DIZAYN tanlandi
# ================================
@router.callback_query(F.data.startswith("design_select_"))
async def select_design(call: CallbackQuery, state: FSMContext):
    num = int(call.data.split("_")[-1])
    await state.update_data(template=num)

    await call.message.answer(
        f"✅ Tanlangan dizayn: {num}\nTasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="design_back")]
        ])
    )
    await call.answer()


# ================================
#  Bekor qilish
# ================================
@router.callback_query(F.data == "design_back")
async def design_back(call: CallbackQuery, state: FSMContext):
    await call.message.answer("❌ Jarayon bekor qilindi. /start dan qayta boshlang.")
    await state.clear()
    await call.answer()


# ================================
#  TASDIQLASH → AI → PPT → Balans yechish
# ================================
@router.callback_query(F.data == "confirm_yes")
async def process_confirmation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = call.from_user.id
    output = None

    try:
        status = await call.message.answer("⏳ AI matn tayyorlamoqda...")

        # AI generatsiya
        slides = await ai_generator.generate_presentation(
            data["topic"],
            data["author"],
            data["slides_count"]
        )

        await status.edit_text("⏳ PPT yaratilmoqda...")

        # PPTX yaratish
        output = await ppt_maker.create_presentation(
            data["topic"],
            data["author"],
            slides,
            data["template"]
        )

        # Balansdan pul yechish
        balance_manager.deduct_balance(
            user_id,
            data["cost"],
            data["slides_count"]
        )

        # Foydalanuvchiga yuborish
        if os.path.exists(output):
            await call.message.answer_document(
                document=FSInputFile(output),
                caption=f"✅ Tayyor!\n💰 {data['cost']:,} so'm yechildi."
            )
        else:
            await call.message.answer("❌ Fayl yaratishda xatolik yuz berdi.")

        await status.delete()
        await state.clear()
        await call.answer()

    except Exception as e:
        logger.error(f"Error in process_confirmation: {e}")
        await call.message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}\n"
            f"Iltimos administratorga murojaat qiling."
        )
        await state.clear()
        await call.answer()
    
    finally:
        # Faylni o'chirish
        if output and os.path.exists(output):
            try:
                os.remove(output)
            except:
                pass
