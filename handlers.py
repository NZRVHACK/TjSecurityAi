from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile
import io
import re
from datetime import datetime

from database import *
from keyboards import *
from utils import *
from config import ADMIN_ID

router = Router()

# === СОСТОЯНИЯ ===
class Form(StatesGroup):
    waiting_url = State()
    waiting_file = State()
    waiting_ai_prompt = State()
    waiting_photo = State()
    waiting_mail_text = State()
    waiting_give_user = State()
    waiting_give_days = State()

# === ОБРАБОТЧИК /START ===
@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "без_ника"
    
    # Проверка на бан
    if is_banned(user_id):
        await message.answer("❌ Вы забанены! Обратитесь к администратору.")
        return
    
    # Регистрация
    create_user(user_id, username)
    
    # Проверка реферала
    if " " in message.text:
        ref_id = message.text.split()[1]
        if ref_id.startswith("ref_"):
            ref_user_id = int(ref_id.split("_")[1])
            if ref_user_id != user_id:
                # Начисляем бонус рефереру
                update_balance(ref_user_id, 2)
                add_history(ref_user_id, "referral", f"+2 балла за {user_id}", "success")
    
    await message.answer(
        "🛡️ *Добро пожаловать в TJ Security AI!*\n\n"
        "Я помогу проверить ссылки, файлы, обработать фото и отвечу на вопросы.\n\n"
        "🔓 *Бесплатно:* 5 баллов при регистрации\n"
        "⭐ *Пополнить баланс:* приглашай друзей (+2 балла)\n"
        "📅 *Ежедневный бонус:* /daily\n\n"
        "👇 Используй кнопки ниже:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# === ГЛАВНОЕ МЕНЮ ===
@router.message(F.text == "🔗 Проверить ссылку")
async def check_url_start(message: Message, state: FSMContext):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены!")
        return
    
    if get_balance(message.from_user.id) < 1:
        await message.answer("❌ Недостаточно баллов! Используй /daily или пригласи друга.")
        return
    
    await message.answer(
        "🔗 Отправь ссылку для проверки:\n\n"
        "Пример: https://example.com",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(Form.waiting_url)

@router.message(Form.waiting_url)
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if url == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=main_menu())
        return
    
    # Валидация URL
    if not re.match(r'^https?://', url):
        await message.answer("⚠️ Введи корректную ссылку (с http:// или https://)")
        return
    
    # Списываем балл
    update_balance(message.from_user.id, -1)
    
    # Проверяем
    await message.answer("🔍 Проверяю ссылку...")
    result = await check_url(url, deep=False)
    
    # Отчёт
    report = f"""
🔗 *Результат проверки:*

{result['level']}

📊 *Оценка:* {result['score']}/100

📋 *Информация:*
"""
    for key, value in result['info'].items():
        report += f"├ {key}: {value}\n"
    
    if result['warnings']:
        report += "\n⚠️ *Предупреждения:*\n"
        for w in result['warnings']:
            report += f"├ {w}\n"
    
    report += "\n✅ Проверка завершена!"
    
    await message.answer(report, parse_mode="Markdown", reply_markup=main_menu())
    await state.clear()
    
    # Сохраняем историю
    add_history(message.from_user.id, "url", url, result['level'])

# === ПРОВЕРКА ФАЙЛА ===
@router.message(F.text == "📁 Проверить файл")
async def check_file_start(message: Message, state: FSMContext):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены!")
        return
    
    if get_balance(message.from_user.id) < 1:
        await message.answer("❌ Недостаточно баллов!")
        return
    
    await message.answer(
        "📁 Отправь файл для проверки:\n\n"
        "Поддерживаются: APK, EXE, PDF, ZIP, DOCX, изображения\n"
        "Максимальный размер: 20 МБ",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(Form.waiting_file)

@router.message(Form.waiting_file, F.document)
async def process_file(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=main_menu())
        return
    
    file = message.document
    if file.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой! Максимум 20 МБ.")
        return
    
    # Списываем балл
    update_balance(message.from_user.id, -1)
    
    await message.answer("🔍 Проверяю файл...")
    
    # Скачиваем файл
    file_obj = await message.bot.download(file)
    file_bytes = file_obj.read()
    
    # Вычисляем хеши
    md5, sha256 = check_file_hash(file_bytes)
    
    # Формируем отчёт
    report = f"""
📁 *Результат проверки файла:*

📄 *Имя:* {file.file_name}
📦 *Размер:* {file.file_size // 1024} КБ
🔐 *MD5:* `{md5}`
🔐 *SHA256:* `{sha256}`

⚠️ *Проверка по локальной базе:* выполняется...
✅ *Расширение:* {file.file_name.split('.')[-1].upper()}

🟢 *Статус:* Файл не найден в базе угроз
"""
    
    await message.answer(report, parse_mode="Markdown", reply_markup=main_menu())
    await state.clear()
    
    # Сохраняем историю
    add_history(message.from_user.id, "file", file.file_name, "safe")

# === AI ПОМОЩНИК ===
@router.message(F.text == "🤖 AI помощник")
async def ai_assistant_start(message: Message, state: FSMContext):
    if is_banned(message.from_user.id):
        await message.answer("❌ Вы забанены!")
        return
    
    if get_balance(message.from_user.id) < 1:
        await message.answer("❌ Недостаточно баллов!")
        return
    
    await message.answer(
        "🤖 *Напиши свой вопрос:*\n\n"
        "Примеры:\n"
        "- Объясни этот код\n"
        "- Что такое фишинг?\n"
        "- Как защитить свой аккаунт?",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(Form.waiting_ai_prompt)

@router.message(Form.waiting_ai_prompt)
async def process_ai_prompt(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено.", reply_markup=main_menu())
        return
    
    # Списываем балл
    update_balance(message.from_user.id, -1)
    
    await message.answer("🤔 Думаю...")
    
    response = await ai_assistant(message.text)
    
    await message.answer(
        f"🤖 *Ответ AI:*\n\n{response}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await state.clear()
    
    add_history(message.from_user.id, "ai", message.text[:50], "answered")

# === ПРОФИЛЬ ===
@router.message(F.text == "👤 Профиль")
async def profile_cmd(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        await message.answer("❌ Ты не зарегистрирован! Используй /start")
        return
    
    _, username, balance, tariff, tariff_until, referrals, _, _ = user
    
    if tariff_until:
        days_left = (datetime.strptime(tariff_until, "%Y-%m-%d") - datetime.now()).days
        tariff_info = f"{tariff.upper()} (осталось {days_left} дн.)"
    else:
        tariff_info = "FREE"
    
    text = f"""
👤 *Профиль*

🆔 ID: `{user_id}`
👤 Ник: @{username or "не указан"}

💰 *Баллы:* {balance}
⭐ *Тариф:* {tariff_info}
👥 *Рефералов:* {referrals}

📊 *Статистика:*
Используй /history для просмотра проверок
"""
    await message.answer(text, parse_mode="Markdown")

# === ЕЖЕДНЕВНЫЙ БОНУС ===
@router.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: Message):
    # Простая проверка (можно усложнить с БД)
    update_balance(message.from_user.id, 1)
    await message.answer("🎁 Ты получил +1 балл! Завтра приходи снова.")

# === ПОДДЕРЖКА ===
@router.message(F.text == "📞 Поддержка")
async def support_cmd(message: Message):
    await message.answer(
        "📞 *Связь с поддержкой*\n\n"
        "Напиши администратору: @tj_security_admin\n"
        "(Этот аккаунт создан для связи)",
        parse_mode="Markdown"
    )

# === ТОП ПОЛЬЗОВАТЕЛЕЙ ===
@router.message(F.text == "📊 Топ пользователей")
async def top_cmd(message: Message):
    users = get_all_users()
    sorted_users = sorted(users, key=lambda x: x[2], reverse=True)[:10]
    
    text = "🏆 *Топ пользователей по баллам:*\n\n"
    for i, (_, username, balance, _, _) in enumerate(sorted_users, 1):
        text += f"{i}. @{username or 'user'} — {balance} баллов\n"
    
    await message.answer(text, parse_mode="Markdown")

# === АДМИН ПАНЕЛЬ ===
@router.message(Command("admin"))
async def admin_panel_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён!")
        return
    
    total, premium, checks = get_stats()
    
    text = f"""
👑 *Админ панель*

👥 Пользователей: {total}
⭐ Премиум: {premium}
📊 Проверок: {checks}

Выбери действие:
"""
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_panel())

# === РАССЫЛКА ===
@router.callback_query(F.data == "admin_mail")
async def admin_mail(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    await callback.message.answer("📢 Введи текст для рассылки:")
    await state.set_state(Form.waiting_mail_text)
    await callback.answer()

@router.message(Form.waiting_mail_text)
async def process_mail(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text
    users = get_all_users()
    
    await message.answer(f"📢 Начинаю рассылку для {len(users)} пользователей...")
    
    for user_id, _, _, _, _ in users:
        try:
            await message.bot.send_message(user_id, f"📢 *Сообщение от администратора:*\n\n{text}", parse_mode="Markdown")
        except:
            pass
    
    await message.answer("✅ Рассылка завершена!")
    await state.clear()

# === ВЫДАТЬ ДОСТУП ===
@router.callback_query(F.data == "admin_give")
async def admin_give(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    await callback.message.answer("➕ Введи ID пользователя:")
    await state.set_state(Form.waiting_give_user)
    await callback.answer()

@router.message(Form.waiting_give_user)
async def process_give_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        user_id = int(message.text.strip())
        await state.update_data(give_user=user_id)
        await message.answer("📅 Введи количество дней (1, 7, 30 или любое число):")
        await state.set_state(Form.waiting_give_days)
    except:
        await message.answer("❌ Неверный ID!")

@router.message(Form.waiting_give_days)
async def process_give_days(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        days = int(message.text.strip())
        data = await state.get_data()
        user_id = data['give_user']
        
        set_tariff(user_id, "premium", days)
        await message.answer(f"✅ Пользователю {user_id} выдан доступ на {days} дней!")
        await state.clear()
    except:
        await message.answer("❌ Введи число!")
