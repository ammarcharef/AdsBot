import logging
import os
import json
import threading
import time
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ==========================================
# ⚙️ إعدادات المشروع العملاق
# ==========================================
TOKEN = "8209432481:AAHwZ7zU8ABj3BNXA-cPrHfJiv3KWxSJ_Jo"
ADMIN_ID = 2140385904

# 🔐 مفتاح سري للتواصل بين البوت والشركة الإعلانية (لحماية البوت من الهكر)
# ستضعه في إعدادات Postback في شركة الإعلانات
SECRET_KEY = "my_secure_secret_123"

# رابط الـ Offerwall الخاص بك (تحصل عليه من شركة الإعلانات مثل Monlix/CPALead)
# يجب أن يحتوي على {user_id} ليقوم البوت باستبداله بآيدي المستخدم
OFFERWALL_URL = "https://www.cpalead.com/dashboard/reports.php?subid={user_id}" 
# ملاحظة: هذا رابط مثال، استبدله برابطك الحقيقي

DB_FILE = "giant_db.json"

# ==========================================
# 💾 قاعدة البيانات
# ==========================================
def load_db():
    default_db = {"users": {}, "withdrawals": [], "total_paid_out": 0.0}
    if not os.path.exists(DB_FILE): return default_db
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return default_db

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_db()

# ==========================================
# 🌐 السيرفر الذكي (Postback Listener)
# ==========================================
# هذا هو "العقل" الذي يستقبل إشارة الربح من الشركات الإعلانية تلقائياً
class PostbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # تحليل الرابط القادم
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)
        
        # 1. استقبال الـ Postback
        # الرابط المتوقع: /postback?uid=12345&amount=0.5&secret=my_secure_secret_123
        if parsed_path.path == "/postback":
            uid = params.get('uid', [None])[0]
            amount = params.get('amount', [None])[0]
            secret = params.get('secret', [None])[0]
            
            # التحقق الأمني (لمنع الهكر من إضافة رصيد لأنفسهم)
            if secret != SECRET_KEY:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden: Wrong Secret")
                return

            if uid and amount and uid in db["users"]:
                try:
                    amt_float = float(amount)
                    # تحويل العملة (إذا كانت الشركة تدفع بالدولار، نضرب في 200 للدينار)
                    dz_amount = amt_float * 200 
                    
                    db["users"][uid]["balance"] += dz_amount
                    db["users"][uid]["total_earned"] += dz_amount
                    save_db(db)
                    
                    print(f"💰 Auto-Earning: User {uid} earned {dz_amount} DZD")
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OK: Balance Added")
                except ValueError:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Error: Invalid Amount")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Error: User Not Found")

        # 2. الصفحة الرئيسية للسيرفر (لإرضاء Render)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Giant Bot Server is Running Securely...")

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), PostbackHandler)
    print(f"🚀 Server listening on port {port}")
    server.serve_forever()

# ==========================================
# 🤖 البوت وتفاعل المستخدمين
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": user.first_name,
            "balance": 0.0,
            "total_earned": 0.0,
            "ccp": None
        }
        save_db(db)

    keyboard = [
        [InlineKeyboardButton("💎 الدخول لساحة المهام (تلقائي)", callback_data='enter_offerwall')],
        [InlineKeyboardButton("💰 محفظتي", callback_data='wallet')],
        [InlineKeyboardButton("❓ شرح النظام", callback_data='help')]
    ]
    
    await update.message.reply_text(
        f"مرحباً {user.first_name} في المنصة الذكية! 🇩🇿\n"
        "هنا النظام يعمل تلقائياً: نفذ المهام -> ينزل الرصيد فوراً.\n\n"
        "اختر ما تريد:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()

    if query.data == 'enter_offerwall':
        # إنشاء رابط خاص للمستخدم
        # نستبدل {user_id} بالآيدي الحقيقي ليتم تعقبه
        personal_link = OFFERWALL_URL.replace("{user_id}", uid)
        
        msg = (
            "🚀 **ساحة المهام والإعلانات**\n\n"
            "اضغط على الرابط أدناه، ستجد قائمة بمهام (تحميل تطبيقات، استبيانات، مشاهدة).\n"
            "✅ بمجرد إكمال المهمة، سيقوم النظام تلقائياً بإضافة الرصيد لمحفظتك هنا.\n\n"
            "⚠️ **تنبيه:** يمنع استخدام VPN."
        )
        keyboard = [[InlineKeyboardButton("🔗 اضغط هنا لبدء الربح", url=personal_link)]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'wallet':
        user_data = db["users"].get(uid)
        bal = user_data['balance']
        ccp_txt = user_data['ccp'] if user_data['ccp'] else "غير مربوط"
        
        txt = (
            f"💰 **محفظتك الشخصية**\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
            f"الرصيد الحالي: **{bal:.2f} دج**\n"
            f"مجموع أرباحك: {user_data['total_earned']:.2f} دج\n"
            f"حساب الدفع: `{ccp_txt}`\n"
        )
        
        btns = [[InlineKeyboardButton("🔙 رجوع", callback_data='back')]]
        if not user_data['ccp']:
            btns.insert(0, [InlineKeyboardButton("📝 ربط CCP", callback_data='set_ccp')])
        elif bal >= 1000:
            btns.insert(0, [InlineKeyboardButton("📤 سحب الرصيد", callback_data='withdraw')])
            
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(btns), parse_mode='Markdown')

    elif query.data == 'set_ccp':
        await query.edit_message_text("أرسل رقم CCP الخاص بك الآن (أرقام فقط):")
        context.user_data['waiting_ccp'] = True

    elif query.data == 'withdraw':
        # عملية سحب تلقائية الطلب
        amount = db["users"][uid]["balance"]
        req = {
            "uid": uid,
            "amount": amount,
            "ccp": db["users"][uid]["ccp"],
            "date": time.strftime("%Y-%m-%d")
        }
        db["withdrawals"].append(req)
        db["users"][uid]["balance"] = 0
        save_db(db)
        
        # إشعار الأدمن
        await context.bot.send_message(
            ADMIN_ID, 
            f"🚨 **سحب جديد!**\nمبلغ: {amount} دج\nCCP: `{req['ccp']}`\nعبر النظام التلقائي."
        )
        await query.edit_message_text("✅ تم إرسال طلب السحب.\nسيصلك إشعار عند التحويل.")

    elif query.data == 'back':
        await start(update, context)

# --- استقبال الرسائل النصية ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_ccp'):
        uid = str(update.effective_user.id)
        ccp = update.message.text
        if ccp.isdigit():
            db["users"][uid]["ccp"] = ccp
            save_db(db)
            context.user_data['waiting_ccp'] = False
            await update.message.reply_text("✅ تم حفظ CCP بنجاح!")
            await start(update, context)
        else:
            await update.message.reply_text("❌ أرقام فقط من فضلك.")

# ==========================================
# 🔥 التشغيل
# ==========================================
if __name__ == '__main__':
    # تشغيل السيرفر في الخلفية لاستقبال الـ Postback
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))
    
    print("Giant Automated Bot Started...")
    app.run_polling()
