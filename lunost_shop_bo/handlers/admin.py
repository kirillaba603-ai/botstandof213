from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import aiosqlite

from database import update_order_status, get_order, add_promocode, delete_promocode, get_all_promocodes, toggle_promocode
from config import EMOJI, ADMIN_ID

router = Router()

WEBAPP_URL = "https://main-five-sage.vercel.app"

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

class PromoAdminStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_discount = State()
    waiting_for_description = State()
    waiting_for_max_uses = State()

def get_webapp_keyboard():
    """Клавиатура с кнопкой веб-приложения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{EMOJI['fire']} Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )

# ============ ОБРАБОТКА ЗАКАЗОВ ============

@router.callback_query(F.data.startswith("admin_accept_"))
async def admin_accept_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав!", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    order = await get_order(order_id)
    
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    await update_order_status(order_id, "completed")
    
    user_text = (
        f"{EMOJI['check']} **Оплата успешно подтверждена!**\n\n"
        f"{EMOJI['package']} **Товар:** {order['product_name']}\n"
        f"{EMOJI['money']} **Сумма:** {order['product_price']}₽\n\n"
        f"{EMOJI['lightning']} Ваш товар будет доставлен в течение **5 минут**!\n"
        f"{EMOJI['heart']} Спасибо за покупку в **LUNO SHOP**!"
    )
    
    await bot.send_message(order["user_id"], user_text, parse_mode="Markdown")
    
    try:
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n✅ **Заказ принят администратором**",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.answer(f"{EMOJI['check']} Заказ #{order_id} принят!")

@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав!", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    order = await get_order(order_id)
    
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    await update_order_status(order_id, "rejected")
    
    user_text = (
        f"{EMOJI['cross']} **Оплата отклонена**\n\n"
        f"{EMOJI['package']} **Товар:** {order['product_name']}\n"
        f"{EMOJI['money']} **Сумма:** {order['product_price']}₽\n\n"
        f"{EMOJI['alert']} **Возможные причины:**\n"
        "• Неверная сумма платежа\n"
        "• Нечитаемый или некорректный чек\n"
        "• Платёж не найден в системе\n\n"
        f"{EMOJI['lightning']} Проверьте данные и попробуйте оформить заказ снова."
    )
    
    await bot.send_message(order["user_id"], user_text, parse_mode="Markdown", reply_markup=get_webapp_keyboard())
    
    try:
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n❌ **Заказ отклонён администратором**",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.answer(f"{EMOJI['cross']} Заказ #{order_id} отклонён!")

@router.callback_query(F.data.startswith("admin_refund_"))
async def admin_refund_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав!", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    order = await get_order(order_id)
    
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    await update_order_status(order_id, "refunded")
    
    user_text = (
        f"❗ **Искренне приносим извинения за доставленные неудобства**\n\n"
        f"{EMOJI['alert']} По заказу **#{order_id}** ({order['product_name']}) обнаружена ошибка в платёжных реквизитах.\n\n"
        f"{EMOJI['money']} **Возврат средств инициирован**\n"
        f"{EMOJI['clock']} Срок возврата: до 3-х рабочих дней\n"
        f"{EMOJI['alert']} Точное время зачисления зависит от вашего банка\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['berry']} **В качестве компенсации** мы дарим вам промокод:\n"
        f"**`REF20`** — скидка **20%** на следующий заказ!\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"{EMOJI['fire']} Чтобы получить товар по **обновлённым реквизитам** и с промокодом, оформите заказ повторно через наш магазин.\n\n"
        f"{EMOJI['heart']} Благодарим за понимание!"
    )
    
    await bot.send_message(order["user_id"], user_text, parse_mode="Markdown", reply_markup=get_webapp_keyboard())
    
    try:
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n💸 **Возврат средств оформлен**",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.answer("💸 Возврат средств оформлен, пользователь уведомлён.")

# ============ КОМАНДЫ АДМИНИСТРАТОРА ============

@router.message(Command("stats"))
async def show_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    async with aiosqlite.connect('shop_bot.db') as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            total_users = (await cursor.fetchone())[0]
        
        async with db.execute('SELECT COUNT(*) FROM orders') as cursor:
            total_orders = (await cursor.fetchone())[0]
        
        async with db.execute('SELECT COUNT(*) FROM orders WHERE status = "completed"') as cursor:
            completed = (await cursor.fetchone())[0]
        
        async with db.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"') as cursor:
            pending = (await cursor.fetchone())[0]
        
        async with db.execute('SELECT SUM(product_price) FROM orders WHERE status = "completed"') as cursor:
            revenue = (await cursor.fetchone())[0] or 0
    
    text = (
        f"{EMOJI['diamond']} **СТАТИСТИКА БОТА**\n\n"
        f"👥 Пользователей: **{total_users}**\n"
        f"📦 Всего заказов: **{total_orders}**\n"
        f"✅ Завершено: **{completed}**\n"
        f"⏳ Ожидают: **{pending}**\n"
        f"💰 Выручка: **{revenue}₽**"
    )
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(BroadcastStates.waiting_for_message)
    await message.answer(
        f"{EMOJI['fire']} **РЕЖИМ РАССЫЛКИ**\n\n"
        "Отправьте сообщение для рассылки.\n"
        "Можно отправить текст, фото или видео.\n\n"
        "/cancel для отмены",
        parse_mode="Markdown"
    )

@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    await message.answer(f"{EMOJI['cross']} Действие отменено")

@router.message(BroadcastStates.waiting_for_message)
async def receive_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    broadcast_data = {
        'text': message.text or message.caption,
        'photo': message.photo[-1].file_id if message.photo else None,
        'video': message.video.file_id if message.video else None,
    }
    
    await state.update_data(broadcast_data=broadcast_data)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    
    async with aiosqlite.connect('shop_bot.db') as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            user_count = (await cursor.fetchone())[0]
    
    text = (
        f"{EMOJI['alert']} **ПОДТВЕРЖДЕНИЕ**\n\n"
        f"Получателей: **{user_count}**\n\n"
        "Отправить?\n"
        "**ДА** - отправить\n"
        "**НЕТ** - отменить"
    )
    
    await message.answer(text, parse_mode="Markdown")

@router.message(BroadcastStates.waiting_for_confirmation)
async def confirm_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text and message.text.upper() == "ДА":
        data = await state.get_data()
        broadcast_data = data.get('broadcast_data')
        
        async with aiosqlite.connect('shop_bot.db') as db:
            async with db.execute('SELECT user_id FROM users') as cursor:
                users = await cursor.fetchall()
        
        success = 0
        failed = 0
        status_msg = await message.answer(f"{EMOJI['lightning']} Рассылка началась...")
        
        for user_id, in users:
            try:
                if broadcast_data['photo']:
                    await bot.send_photo(
                        user_id,
                        photo=broadcast_data['photo'],
                        caption=broadcast_data['text'],
                        parse_mode="Markdown"
                    )
                elif broadcast_data['video']:
                    await bot.send_video(
                        user_id,
                        video=broadcast_data['video'],
                        caption=broadcast_data['text'],
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_message(
                        user_id,
                        text=broadcast_data['text'],
                        parse_mode="Markdown"
                    )
                success += 1
            except:
                failed += 1
        
        await status_msg.edit_text(
            f"{EMOJI['check']} **Рассылка завершена!**\n\n"
            f"✅ Успешно: **{success}**\n"
            f"❌ Ошибок: **{failed}**",
            parse_mode="Markdown"
        )
        await state.clear()
    
    elif message.text and message.text.upper() == "НЕТ":
        await message.answer(f"{EMOJI['cross']} Рассылка отменена")
        await state.clear()
    
    else:
        await message.answer("Ответьте **ДА** или **НЕТ**", parse_mode="Markdown")

@router.message(Command("refund"))
async def manual_refund(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        # Извлекаем все ID после команды
        ids_text = message.text.replace("/refund", "").strip()
        
        if not ids_text:
            await message.answer(
                f"{EMOJI['alert']} **Использование:**\n"
                "`/refund ID1, ID2, ID3...`\n\n"
                "Примеры:\n"
                "• `/refund 5` — один заказ\n"
                "• `/refund 5, 7, 12` — несколько заказов",
                parse_mode="Markdown"
            )
            return
        
        # Разделяем по запятой и убираем пробелы
        order_ids = [int(id.strip()) for id in ids_text.split(",")]
        
        success_count = 0
        failed_count = 0
        results = []
        
        status_msg = await message.answer(
            f"{EMOJI['lightning']} Обработка возвратов...\n"
            f"Всего заказов: {len(order_ids)}",
            parse_mode="Markdown"
        )
        
        for order_id in order_ids:
            try:
                order = await get_order(order_id)
                
                if not order:
                    results.append(f"❌ #{order_id} — не найден")
                    failed_count += 1
                    continue
                
                await update_order_status(order_id, "refunded")
                
                user_text = (
                    f"❗ **Искренне приносим извинения за доставленные неудобства**\n\n"
                    f"{EMOJI['alert']} По заказу **#{order_id}** ({order['product_name']}) обнаружена ошибка в платёжных реквизитах.\n\n"
                    f"{EMOJI['money']} **Возврат средств инициирован**\n"
                    f"{EMOJI['clock']} Срок возврата: до 3-х рабочих дней\n"
                    f"{EMOJI['alert']} Точное время зачисления зависит от вашего банка\n\n"
                    f"━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{EMOJI['berry']} **В качестве компенсации** мы дарим вам промокод:\n"
                    f"**`REF20`** — скидка **20%** на следующий заказ!\n\n"
                    f"━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{EMOJI['fire']} Чтобы получить товар по **обновлённым реквизитам** и с промокодом, оформите заказ повторно через наш магазин.\n\n"
                    f"{EMOJI['heart']} Благодарим за понимание!"
                )
                
                await bot.send_message(
                    order["user_id"], 
                    user_text, 
                    parse_mode="Markdown", 
                    reply_markup=get_webapp_keyboard()
                )
                
                results.append(f"✅ #{order_id} — возврат оформлен")
                success_count += 1
                
            except Exception as e:
                results.append(f"❌ #{order_id} — ошибка: {str(e)}")
                failed_count += 1
        
        # Формируем итоговый отчёт
        report = (
            f"{EMOJI['check']} **ОТЧЁТ О ВОЗВРАТАХ**\n\n"
            f"✅ Успешно: **{success_count}**\n"
            f"❌ Ошибок: **{failed_count}**\n\n"
            f"**Детали:**\n"
        )
        
        for result in results:
            report += f"{result}\n"
        
        await status_msg.edit_text(report, parse_mode="Markdown")
    
    except ValueError:
        await message.answer(
            f"{EMOJI['cross']} **Ошибка формата!**\n\n"
            "ID заказов должны быть числами.\n"
            "Используйте: `/refund 5, 7, 12`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"{EMOJI['cross']} Ошибка: {str(e)}")

# ============ ПРОМОКОДЫ ============

@router.message(Command("addpromo"))
async def start_add_promo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(PromoAdminStates.waiting_for_code)
    await message.answer(
        f"{EMOJI['berry']} **СОЗДАНИЕ ПРОМОКОДА**\n\n"
        "Шаг 1/4: Введите код промокода\n"
        "_(Например: FREE10)_",
        parse_mode="Markdown"
    )

@router.message(PromoAdminStates.waiting_for_code)
async def get_promo_code(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    code = message.text.strip().upper()
    await state.update_data(promo_code=code)
    await state.set_state(PromoAdminStates.waiting_for_discount)
    await message.answer(
        "Шаг 2/4: Введите размер скидки в %\n"
        "_(Например: 10)_",
        parse_mode="Markdown"
    )

@router.message(PromoAdminStates.waiting_for_discount)
async def get_promo_discount(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        discount = int(message.text.strip())
        await state.update_data(discount=discount)
        await state.set_state(PromoAdminStates.waiting_for_description)
        await message.answer("Шаг 3/4: Введите описание", parse_mode="Markdown")
    except:
        await message.answer(f"{EMOJI['cross']} Введите число!")

@router.message(PromoAdminStates.waiting_for_description)
async def get_promo_desc(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.update_data(description=message.text.strip())
    await state.set_state(PromoAdminStates.waiting_for_max_uses)
    await message.answer("Шаг 4/4: Макс. использований (0 = безлимит)", parse_mode="Markdown")

@router.message(PromoAdminStates.waiting_for_max_uses)
async def create_promo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        max_uses = int(message.text.strip())
        data = await state.get_data()
        
        success = await add_promocode(
            data['promo_code'],
            data['discount'],
            data['description'],
            max_uses
        )
        
        if success:
            await message.answer(
                f"{EMOJI['check']} **Промокод создан!**\n\n"
                f"Код: `{data['promo_code']}`\n"
                f"Скидка: {data['discount']}%",
                parse_mode="Markdown"
            )
        else:
            await message.answer(f"{EMOJI['cross']} Такой промокод уже существует!")
        
        await state.clear()
    except:
        await message.answer(f"{EMOJI['cross']} Введите число!")

@router.message(Command("promos"))
async def list_promos(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    promos = await get_all_promocodes()
    
    if not promos:
        await message.answer("Промокодов пока нет.\n\n/addpromo для создания")
        return
    
    text = f"{EMOJI['berry']} **ПРОМОКОДЫ**\n\n"
    for p in promos:
        text += f"`{p['code']}` - {p['discount']}% ({'🟢' if p['is_active'] else '🔴'})\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("delpromo"))
async def delete_promo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        code = message.text.split()[1].upper()
        await delete_promocode(code)
        await message.answer(f"{EMOJI['check']} Промокод удалён!")
    except:
        await message.answer("Использование: /delpromo КОД")

@router.message(Command("togglepromo"))
async def toggle_promo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        code = message.text.split()[1].upper()
        await toggle_promocode(code)
        await message.answer(f"{EMOJI['check']} Статус изменён!")
    except:
        await message.answer("Использование: /togglepromo КОД")
