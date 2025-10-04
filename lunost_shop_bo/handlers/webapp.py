from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json

from config import ADMIN_ID
from database import create_order, update_order_photo
from keyboards import get_admin_decision

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_photo = State()

@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext, bot: Bot):
    try:
        data = json.loads(message.web_app_data.data)
        
        # Сохраняем все данные
        await state.update_data(
            product_id=data.get('product_id'),
            product_name=data.get('product_name'),
            base_price=data.get('original_price', data.get('price')),
            final_price=data.get('price'),
            promo_code=data.get('promo_code'),
            payment_method=data.get('payment_method', 'unknown')
        )
        
        # Переходим к ожиданию фото
        await state.set_state(PaymentStates.waiting_for_photo)
        
        text = "✅ Заказ оформлен!\n\n"
        text += f"📦 Товар: {data.get('product_name')}\n"
        text += f"💰 Цена: {data.get('price')}₽\n"
        
        if data.get('promo_code'):
            text += f"🎫 Промокод: {data.get('promo_code')}\n"
        
        text += f"\n✈️ Отправьте фото чека или скриншот оплаты\n\n"
        text += f"📸 Требования:\n"
        text += f"• Чек должен быть четким\n"
        text += f"• Видна сумма и дата\n\n"
        text += f"⚡️ После проверки (5-15 мин) вы получите товар!"
        
        await message.answer(text)
        
    except Exception as e:
        print(f"Ошибка обработки Mini App: {e}")
        await message.answer("❌ Ошибка. Попробуйте снова через кнопку 'Открыть магазин'")

@router.message(PaymentStates.waiting_for_photo, F.photo)
async def process_payment_photo(message: Message, state: FSMContext, bot: Bot):
    # Получаем данные
    data = await state.get_data()
    
    print(f"DEBUG: Данные из state: {data}")  # Для отладки
    
    product_name = data.get('product_name')
    final_price = data.get('final_price')
    base_price = data.get('base_price', final_price)
    promo_code = data.get('promo_code')
    payment_method = data.get('payment_method', 'unknown')
    
    # Проверка наличия данных
    if not product_name or not final_price:
        await message.answer(
            "❌ Данные заказа потеряны.\n"
            "Пожалуйста, начните заново:\n"
            "1. Нажмите 'Открыть магазин'\n"
            "2. Выберите товар\n"
            "3. Нажмите 'Оплатил'\n"
            "4. Отправьте чек"
        )
        await state.clear()
        return
    
    # Создаём заказ
    order_id = await create_order(
        message.from_user.id, 
        product_name, 
        final_price, 
        payment_method,
        base_price, 
        promo_code
    )
    
    photo_file_id = message.photo[-1].file_id
    await update_order_photo(order_id, photo_file_id)
    
    # Сообщение админу
    admin_text = f"⚠️ НОВЫЙ ЗАКАЗ #{order_id}\n\n"
    admin_text += f"📦 Товар: {product_name}\n"
    admin_text += f"💰 Цена: {final_price}₽\n"
    
    if promo_code:
        discount = base_price - final_price
        admin_text += f"🎫 Промокод: {promo_code}\n"
        admin_text += f"💵 Без скидки: {base_price}₽\n"
        admin_text += f"💚 Скидка: {discount}₽\n"
    
    admin_text += f"💳 Метод: {payment_method}\n\n"
    admin_text += f"👤 Покупатель:\n"
    
    if message.from_user.username:
        admin_text += f"Username: @{message.from_user.username}\n"
    
    admin_text += f"Имя: {message.from_user.first_name}\n"
    admin_text += f"ID: {message.from_user.id}"
    
    await bot.send_photo(
        ADMIN_ID, 
        photo=photo_file_id, 
        caption=admin_text, 
        reply_markup=get_admin_decision(order_id)
    )
    
    # Сообщение пользователю
    user_text = "✅ ЧЕК ПОЛУЧЕН!\n\n"
    user_text += f"✓ Заказ №{order_id} на проверке\n"
    user_text += f"⏱ Время проверки: 5-15 минут\n"
    user_text += f"📬 Вы получите уведомление\n\n"
    user_text += f"🖤 Спасибо за ожидание!"
    
    await message.answer(user_text)
    await state.clear()

@router.message(PaymentStates.waiting_for_photo)
async def wrong_content(message: Message):
    await message.answer(
        "❌ Отправьте ФОТО чека\n\n"
        "📸 Принимается:\n"
        "• Скриншот из банка\n"
        "• Фото чека\n"
        "• Подтверждение перевода"
    )
