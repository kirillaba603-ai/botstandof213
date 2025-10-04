import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ТОКЕН И ID НАПРЯМУЮ (самый простой способ)
BOT_TOKEN = '8280868767:AAGmm2kb5F7MI5I-uTWlzxZFxH550IpGfAM'
ADMIN_ID = 6530644564

# Реквизиты для оплаты
PAYMENT_CARD = "2204120120046764"
PAYMENT_YOOMONEY = "4100118918710456"
PAYMENT_SBP_PHONE = "+79969428462"
PAYMENT_SBP_NAME = "Кривошапкин Николай Николаевич"
PAYMENT_SBP_BANK = "ЮMoney"

# Эмодзи для дизайна
EMOJI = {
    'fire': '🔥',
    'star': '⭐',
    'diamond': '💎',
    'check': '✅',
    'cross': '❌',
    'money': '💰',
    'card': '💳',
    'arrow': '➡️',
    'back': '◀️',
    'cart': '🛒',
    'package': '📦',
    'heart': '🖤',
    'alert': '‼️',
    'lock': '🔒',
    'lightning': '⚡️',
    'berry': '🍓',
    'plane': '✈️',
    'purple': '💜',
    'wind': '💨',
    'clock': '⏱'
}

# Вывод конфигурации при запуске
print(f"✓ Токен бота загружен: {BOT_TOKEN[:10]}...")
print(f"✓ ADMIN_ID: {ADMIN_ID}")
print(f"✓ Реквизиты оплаты настроены")
