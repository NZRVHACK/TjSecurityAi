from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🔗 Проверить ссылку")],
            [KeyboardButton("📁 Проверить файл")],
            [KeyboardButton("🤖 AI помощник")],
            [KeyboardButton("🖼 Работа с фото")],
            [KeyboardButton("👤 Профиль"), KeyboardButton("⭐ Тариф")],
            [KeyboardButton("📞 Поддержка"), KeyboardButton("📊 Топ пользователей")],
            [KeyboardButton("🎁 Ежедневный бонус")]
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("❌ Отмена")]],
        resize_keyboard=True
    )

def danger_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔴 ОПАСНО! Заблокировать", callback_data="block")],
            [InlineKeyboardButton("🔵 Информация", callback_data="info")],
            [InlineKeyboardButton("🟢 Безопасно", callback_data="safe")]
        ]
    )

def admin_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("➕ Выдать доступ", callback_data="admin_give")],
            [InlineKeyboardButton("➖ Забрать доступ", callback_data="admin_take")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_mail")],
            [InlineKeyboardButton("⚙️ Чёрный список", callback_data="admin_blacklist")]
        ]
    )

def check_modes():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🟢 Быстрая проверка (1 балл)", callback_data="check_fast")],
            [InlineKeyboardButton("🔴 Глубокая проверка (2 балла)", callback_data="check_deep")]
        ]
    )

def photo_modes():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🟣 Удалить фон", callback_data="photo_bg")],
            [InlineKeyboardButton("🟣 Стиль киберпанк", callback_data="photo_cyber")],
            [InlineKeyboardButton("🟣 Улучшить качество", callback_data="photo_enhance")],
            [InlineKeyboardButton("🟣 Восстановить фото", callback_data="photo_restore")]
        ]
    )
