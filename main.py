import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# --- الإعدادات (املأها بمعلوماتك) ---
TOKEN = "8107998664:AAFp-OrBQnG7hIzD4iQccvs9xJbIfAuEZHE"  # احصل عليه من BotFather
ADMIN_ID = 2140385904  # ضع الآيدي الخاص بك هنا (يمكنك معرفته من بوتات كشف الآيدي)

# --- قاعدة بيانات مؤقتة (في الذاكرة) ---
# ملاحظة: للمشاريع الكبيرة نستخدم ملف قاعدة بيانات حقيقي، هنا للتبسيط فقط
users_db = {}  # لتخزين: {user_id: balance}

# --- الدوال الأساسية ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # تسجيل المستخدم الجديد بصفر دينار
    if user_id not in users_db:
        users_db[user_id] = 0.0

    # تصميم القائمة الرئيسية
    keyboard = [
        [InlineKeyboardButton("👁️ مشاهدة إعلان (كسب المال)", callback_data='watch_ad')],
        [InlineKeyboardButton("💰 رصيدي", callback_data='balance')],
        [InlineKeyboardButton("💳 طلب سحب (CCP/Baridi)", callback_data='withdraw')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"مرحباً بك يا {first_name} في بوت الربح من الإعلانات.\n"
        "اضغط على الأزرار للبدء:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # --- قسم مشاهدة الإعلانات ---
    if query.data == 'watch_ad':
        # هنا تضع رابط الإعلان الحقيقي لاحقاً
        # سنقوم بمحاكاة أن المستخدم شاهد إعلان وربح 2 دينار
        users_db[user_id] += 2.0  # إضافة الرصيد
        await query.edit_message_text(
            text="✅ تم مشاهدة الإعلان بنجاح!\nتم إضافة 2 دج إلى رصيدك.\n\nانتظر قليلاً للإعلان التالي...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة للقائمة", callback_data='back')]])
        )

    # --- قسم الرصيد ---
    elif query.data == 'balance':
        balance = users_db.get(user_id, 0)
        await query.edit_message_text(
            text=f"💰 رصيدك الحالي هو: {balance} دج",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة", callback_data='back')]])
        )

    # --- زر العودة ---
    elif query.data == 'back':
        # إعادة عرض القائمة الرئيسية
        keyboard = [
            [InlineKeyboardButton("👁️ مشاهدة إعلان", callback_data='watch_ad')],
            [InlineKeyboardButton("💰 رصيدي", callback_data='balance')],
            [InlineKeyboardButton("💳 سحب", callback_data='withdraw')],
        ]
        await query.edit_message_text(
            text="القائمة الرئيسية:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif query.data == 'withdraw':
         await query.edit_message_text(
            text="⚠️ الحد الأدنى للسحب هو 500 دج.\nعند الوصول للمبلغ تواصل مع الإدارة.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة", callback_data='back')]])
        )

# --- تشغيل البوت ---
if __name__ == '__main__':
    # بناء التطبيق
    application = ApplicationBuilder().token(TOKEN).build()
    
    # ربط الدوال بالأوامر
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    # تشغيل البوت بشكل مستمر (Polling)
    application.run_polling()