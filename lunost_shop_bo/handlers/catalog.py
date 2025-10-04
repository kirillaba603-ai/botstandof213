from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards import get_cheats_category, get_gold_category, get_payment_methods, get_main_menu
from config import EMOJI

router = Router()

CHEAT_PHOTO = "photo_2025-10-02_00-49-38.jpg"
GOLD_PHOTO = "photo_2025-10-02_00-49-55.jpg"

class PromoStates(StatesGroup):
    waiting_for_promo = State()

PRODUCTS = {
    'cheat_1': {
        'name': 'ВХ ЧЕРЕЗ СТЕНЫ - СКИНЧЕНДЖЕР',
        'price': 150,
        'description': f"{EMOJI['heart']} Luno APK - приватный DLC\n{EMOJI['alert']} Не требует Root\n{EMOJI['lightning']} Быстрые обновления"
    },
    'cheat_2': {
        'name': 'АДМИН ПАНЕЛЬ + ВСЕ ФУНКЦИИ',
        'price': 300,
        'description': f"{EMOJI['heart']} Полный доступ\n{EMOJI['lock']} Максимальная безопасность\n{EMOJI['lightning']} Поддержка 24/7"
    },
    'cheat_3': {
        'name': 'ПАНЕЛЬ РАЗРАБА + ВЫДАЧА ГОЛДЫ',
        'price': 500,
        'description': f"{EMOJI['heart']} Все возможности\n{EMOJI['diamond']} Выдача голды\n{EMOJI['fire']} VIP функции"
    },
    'gold_1': {
        'name': '500 GOLD',
        'price': 150,
        'description': f"{EMOJI['berry']} СКИДКА 60%!\n{EMOJI['money']} 500 золотых монет\n{EMOJI['lightning']} Моментально"
    },
    'gold_2': {
        'name': '1000 GOLD',
        'price': 250,
        'description': f"{EMOJI['berry']} СКИДКА 60%!\n{EMOJI['money']} 1000 золотых монет\n{EMOJI['lightning']} Моментально"
    },
    'gold_3': {
        'name': '3000 GOLD',
        'price': 399,
        'description': f"{EMOJI['berry']} СКИДКА 60%!\n{EMOJI['diamond']} 3000 золотых монет\n{EMOJI['alert']} Ограничено"
    }
}

@router.callback_query(F.data == "category_cheats")
async def show_cheats(callback: CallbackQuery):
    text = f"{EMOJI['fire']} **ЛУЧШИЕ ЧИТЫ**\nВыберите товар:"
    photo = FSInputFile(CHEAT_PHOTO)
    await callback.message.delete()
    await callback.message.answer_photo(photo=photo, caption=text, reply_markup=get_cheats_category(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "category_gold")
async def show_gold(callback: CallbackQuery):
    text = f"{EMOJI['money']} **ГОЛДА НА БАЛАНС**\n{EMOJI['berry']} Скидка 60%!\nВыберите количество:"
    photo = FSInputFile(GOLD_PHOTO)
    await callback.message.delete()
    await callback.message.answer_photo(photo=photo, caption=text, reply_markup=get_gold_category(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.replace("product_", "")
    
    if product_id in PRODUCTS:
        product = PRODUCTS[product_id]
        await state.update_data(product_id=product_id, base_price=product['price'], final_price=product['price'], promo_code=None)
        
        text = f"{EMOJI['package']} **{product['name']}**\n\n{product['description']}\n\n{EMOJI['star']} У вас есть промокод?"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{EMOJI['berry']} Ввести промокод", callback_data=f"enter_promo_{product_id}")],
            [InlineKeyboardButton(text=f"{EMOJI['arrow']} Перейти к оплате", callback_data=f"skip_promo_{product_id}")],
            [InlineKeyboardButton(text=f"{EMOJI['back']} Назад", callback_data="back_from_payment")]
        ])
        
        await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="Markdown")
    
    await callback.answer()

@router.callback_query(F.data.startswith("enter_promo_"))
async def enter_promo_code(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_promo)
    text = f"{EMOJI['berry']} **ВВОД ПРОМОКОДА**\n\nОтправьте промокод в чат"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("skip_promo_"))
async def skip_promo(callback: CallbackQuery):
    product_id = callback.data.replace("skip_promo_", "")
    text = f"{EMOJI['arrow']} **Выберите способ оплаты:**"
    
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_payment_methods(product_id), parse_mode="Markdown")
    except:
        try:
            await callback.message.edit_text(text, reply_markup=get_payment_methods(product_id), parse_mode="Markdown")
        except:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=get_payment_methods(product_id), parse_mode="Markdown")
    
    await callback.answer()

@router.callback_query(F.data == "back_from_payment")
async def back_from_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    
    text = f"{EMOJI['fire']} **LUNOST SHOP**\n\nВыберите категорию:"
    await callback.message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    await callback.answer()
