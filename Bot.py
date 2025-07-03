import logging
import json
import os
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler,
    ConversationHandler, ContextTypes
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

USERS_FILE = "users_data.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# Стани
(
    REG_NAME,
    REG_PHONE,
    CHOOSE_CLASS_TYPE,
    CHOOSE_DIRECTION,
    CHOOSE_TEACHER,
    SHOW_INFO
) = range(6)

VOCAL_DIRECTIONS = ["Поп", "Академічний", "Рок", "Джаз"]
CLASS_TYPES = ["Індивідуальне заняття", "Групове заняття", "Пробний урок"]

TEACHERS = {
    "Ярослава": {
        "style": "Джаз, Поп, Рок",
        "bio": "Ярослава — викладачка з 10 роками досвіду.",
        "price": "300 грн",
        "classes_info": {
            "Індивідуальне заняття": "Індивідуальні заняття з акцентом на твій стиль.",
            "Групове заняття": "Заняття у групі до 5 осіб, весело та продуктивно.",
            "Пробний урок": "Пробний урок, щоб зрозуміти рівень та інтереси."
        }
    },
    "Олег": {
        "style": "Академічний",
        "bio": "Олег — лауреат конкурсів.",
        "price": "350 грн",
        "classes_info": {
            "Індивідуальне заняття": "Індивідуальний підхід з класичним вокалом.",
            "Групове заняття": "Групове навчання академічному вокалу.",
            "Пробний урок": "Пробний урок для знайомства."
        }
    },
    "Марина": {
        "style": "Джаз",
        "bio": "Марина — джазова вокалістка, 7 років стажу.",
        "price": "320 грн",
        "classes_info": {
            "Індивідуальне заняття": "Фокус на джазовий вокал в індивідуальному режимі.",
            "Групове заняття": "Група для вивчення джазових імпровізацій.",
            "Пробний урок": "Пробний урок для новачків."
        }
    }
}

# Завантажуємо користувачів з файлу
users = load_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    if user_id in users and "name" in users[user_id] and "phone" in users[user_id]:
        # Якщо користувач вже зареєстрований
        await update.message.reply_text(
            f"Вітаю, {users[user_id]['name']}! Ти вже зареєстрований.\n"
            "Якщо хочеш змінити інформацію, надішли /restart, або /cancel для виходу."
        )
        return ConversationHandler.END
    else:
        logger.info(f"User {user_id} started registration.")
        await update.message.reply_text("Привіт! Як тебе звати?")
        return REG_NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    name = update.message.text
    users[user_id] = {"name": name}
    save_users(users)
    logger.info(f"User {user_id} set name: {name}")

    button = KeyboardButton("Поділитись контактом", request_contact=True)
    await update.message.reply_text(
        "Поділись номером телефону:",
        reply_markup=ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    )
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    users[user_id]["phone"] = phone
    save_users(users)
    logger.info(f"User {user_id} set phone: {phone}")

    await update.message.reply_text(
        "Що тебе цікавить?",
        reply_markup=ReplyKeyboardMarkup([CLASS_TYPES], resize_keyboard=True, one_time_keyboard=True)
    )
    return CHOOSE_CLASS_TYPE

async def choose_class_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    class_type = update.message.text
    if class_type not in CLASS_TYPES:
        await update.message.reply_text("Будь ласка, обери з наданих варіантів.")
        return CHOOSE_CLASS_TYPE

    users[user_id]["class_type"] = class_type
    save_users(users)
    logger.info(f"User {user_id} chose class type: {class_type}")

    keyboard = [VOCAL_DIRECTIONS, ["⬅ Назад"]]
    await update.message.reply_text(
        "Оберіть напрямок вокалу:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CHOOSE_DIRECTION

async def choose_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    direction = update.message.text

    if direction == "⬅ Назад":
        await update.message.reply_text(
            "Що тебе цікавить?",
            reply_markup=ReplyKeyboardMarkup([CLASS_TYPES], resize_keyboard=True, one_time_keyboard=True)
        )
        return CHOOSE_CLASS_TYPE

    if direction not in VOCAL_DIRECTIONS:
        await update.message.reply_text("Будь ласка, обери з наданих напрямків.")
        return CHOOSE_DIRECTION

    users[user_id]["direction"] = direction
    save_users(users)
    logger.info(f"User {user_id} chose direction: {direction}")

    filtered_teachers = [name for name, data in TEACHERS.items() if direction in data["style"]]

    if not filtered_teachers:
        await update.message.reply_text("Вибачте, немає викладачів для цього напрямку.")
        return CHOOSE_DIRECTION

    buttons = [[InlineKeyboardButton(name, callback_data=name)] for name in filtered_teachers]
    buttons.append([InlineKeyboardButton("⬅ Назад", callback_data="BACK_TO_DIRECTION")])

    await update.message.reply_text("Оберіть викладача:", reply_markup=InlineKeyboardMarkup(buttons))
    return CHOOSE_TEACHER

async def choose_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data

    if data == "BACK_TO_DIRECTION":
        await query.edit_message_text(
            "Оберіть напрямок вокалу:",
            reply_markup=ReplyKeyboardMarkup([VOCAL_DIRECTIONS, ["⬅ Назад"]], resize_keyboard=True, one_time_keyboard=True)
        )
        return CHOOSE_DIRECTION

    users[user_id]["teacher"] = data
    save_users(users)
    info = TEACHERS[data]
    class_type = users[user_id]["class_type"]
    class_info = info["classes_info"].get(class_type, "Інформація відсутня")

    logger.info(f"User {user_id} chose teacher: {data} for class type: {class_type}")

    message = (
        f"Викладач: {data}\n"
        f"Стиль: {info['style']}\n"
        f"Про викладача: {info['bio']}\n"
        f"Ціна: {info['price']}\n\n"
        f"Інформація про '{class_type}':\n{class_info}\n\n"
        "Якщо хочеш, можеш /start або /cancel"
    )
    await query.edit_message_text(message)
    return SHOW_INFO

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id) if update.message else None
    logger.info(f"User {user_id} canceled conversation.")
    await update.message.reply_text("Реєстрацію скасовано.")
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    # Видаляємо дані користувача, щоб пройти реєстрацію заново
    if user_id in users:
        del users[user_id]
        save_users(users)
    await update.message.reply_text("Реєстрація починається заново. Як тебе звати?")
    return REG_NAME

def main():
    app = ApplicationBuilder().token("7305961255:AAGdr7DTKMzs_HOQhgkF0wN0doVcvQiRXJY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), reg_name)],
            REG_PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, reg_phone)],
            CHOOSE_CLASS_TYPE: [MessageHandler(filters.TEXT & (~filters.COMMAND), choose_class_type)],
            CHOOSE_DIRECTION: [MessageHandler(filters.TEXT & (~filters.COMMAND), choose_direction)],
            CHOOSE_TEACHER: [CallbackQueryHandler(choose_teacher)],
            SHOW_INFO: [MessageHandler(filters.TEXT & (~filters.COMMAND), cancel)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("restart", restart)
        ]
    )

    app.add_handler(conv_handler)

    print("Bot started polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
