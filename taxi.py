import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import re
from datetime import datetime

# Bot konfiguratsiyasi
BOT_TOKEN = "7979548630:AAHOYkj4sfNoKegA5gk7jpxx8hLoTnSmsq0"
CHANNEL_ID = "https://t.me/i_tech_team"  # Kanal username yoki ID

# Holatlar
NAME, PHONE, LOCATION, CONFIRMATION = range(4)

# Log konfiguratsiyasi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Foydalanuvchi ma'lumotlarini saqlash uchun vaqtinchalik xotira
user_data = {}
orders = {}  # Buyurtmalarni saqlash uchun

# Botni ishga tushirish
async def start(update: Update, context):
    await update.message.reply_text(
        "Assalomu alaykum! Taksibotga xush kelibsiz.\n"
        "Ismingizni kiriting:"
    )
    return NAME

# Ismni qayta ishlash
async def get_name(update: Update, context):
    user_id = update.message.from_user.id
    user_data[user_id] = {'name': update.message.text}
    
    await update.message.reply_text("Telefon raqamingizni kiriting (masalan: +998901234567):")
    return PHONE

# Telefon raqamini qayta ishlash
async def get_phone(update: Update, context):
    user_id = update.message.from_user.id
    phone = update.message.text
    
    # Telefon raqamini tekshirish (O'zbekiston raqamlari uchun)
    if not re.match(r'^\+998\d{2}\d{3}\d{2}\d{2}$', phone):
        await update.message.reply_text("Iltimos, to'g'ri formatda telefon raqamini kiriting (masalan: +998901234567):")
        return PHONE
    
    user_data[user_id]['phone'] = phone
    await update.message.reply_text("Manzilingizni kiriting:")
    return LOCATION

# Manzilni qayta ishlash
async def get_location(update: Update, context):
    user_id = update.message.from_user.id
    user_data[user_id]['location'] = update.message.text
    user_data[user_id]['user_id'] = user_id
    user_data[user_id]['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Ma'lumotlarni tasdiqlash
    keyboard = [
        [InlineKeyboardButton("Ha", callback_data="confirm_yes")],
        [InlineKeyboardButton("Yo'q", callback_data="confirm_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    info = f"Quyidagi ma'lumotlarni tasdiqlaysizmi?\n\n" \
           f"Ism: {user_data[user_id]['name']}\n" \
           f"Telefon: {user_data[user_id]['phone']}\n" \
           f"Manzil: {user_data[user_id]['location']}"
    
    await update.message.reply_text(info, reply_markup=reply_markup)
    return CONFIRMATION

# Tasdiqlash tugmasi bosilganda
async def confirmation(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "confirm_yes":
        # Buyurtma ID sini yaratish
        order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        orders[order_id] = user_data[user_id].copy()
        orders[order_id]['order_id'] = order_id
        
        # Ma'lumotlarni kanalga yuborish
        message_text = f"🚖 Yangi buyurtma! #{order_id}\n\n" \
                       f"👤 Ism: {user_data[user_id]['name']}\n" \
                       f"📞 Telefon: {user_data[user_id]['phone']}\n" \
                       f"📍 Manzil: {user_data[user_id]['location']}\n\n" \
                       f"🕒 Vaqti: {user_data[user_id]['timestamp']}\n\n" \
                       f"Buyurtmani qabul qilish uchun quyidagi tugmani bosing."
        
        # Kanalga yuborish uchun tugma
        keyboard = [
            [InlineKeyboardButton("✅ Qabul qilish", callback_data=f"accept_{order_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Xabarni kanalga yuborish
        try:
            await context.bot.send_message(
                chat_id="@i_tech_team",
                text=message_text,
                reply_markup=reply_markup
            )
            await query.edit_message_text("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.")
        except Exception as e:
            await query.edit_message_text("❌ Xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")
            logging.error(f"Xatolik: {e}")
        
    else:
        await query.edit_message_text("Ma'lumotlaringiz qayta kiritilishi kerak. /start ni bosing.")
    
    # Foydalanuvchi ma'lumotlarini tozalash
    if user_id in user_data:
        del user_data[user_id]
        
    return ConversationHandler.END

# Kanalda "Qabul qilish" tugmasi bosilganda
async def accept_order(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    # Buyurtma ID sini olish
    data_parts = query.data.split('_')
    order_id = data_parts[1]
    
    if order_id not in orders:
        await query.edit_message_text("❌ Bu buyurtma allaqachon qabul qilingan yoki mavjud emas.")
        return
    
    # Qabul qilgan taksichi haqida ma'lumot
    driver_name = query.from_user.first_name
    if query.from_user.username:
        driver_name += f" (@{query.from_user.username})"
    
    # Xabarni yangilash
    original_text = query.message.text
    new_text = f"{original_text}\n\n🚗 Buyurtmani qabul qildi: {driver_name}"
    
    await query.edit_message_text(new_text)
    
    # Taksichiga mijoz telefon raqamini yuborish
    customer_phone = orders[order_id]['phone']
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=f"🎉 Siz yangi buyurtmani qabul qildingiz!\n\n"
             f"📞 Mijoz telefon raqami: {customer_phone}\n"
             f"👤 Mijoz ismi: {orders[order_id]['name']}\n"
             f"📍 Manzil: {orders[order_id]['location']}\n\n"
             f"✅ Iltimos, tez orada mijoz bilan bog'laning!"
    )
    
    # Buyurtmani ro'yxatdan o'chirish
    del orders[order_id]

# Xatolik yuz berganda
async def error(update: Update, context):
    logging.error(f"Update {update} caused error {context.error}")

# Asosiy funksiya
def main():
    # Botni yaratish
    application = Application.builder().token("7979548630:AAHOYkj4sfNoKegA5gk7jpxx8hLoTnSmsq0").build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            CONFIRMATION: [CallbackQueryHandler(confirmation)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    # Handlerlarni qo'shish
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(accept_order, pattern=r"accept_"))
    application.add_error_handler(error)
    
    # Botni ishga tushirish
    application.run_polling()
    print("Bot ishga tushdi...")

if __name__ == '__main__':
    main()
