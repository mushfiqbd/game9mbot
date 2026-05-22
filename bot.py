import os
import re
import time
import threading
import schedule
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@game9m")
LANDING_PAGE_URL = os.getenv("LANDING_PAGE_URL", "https://game9m.live")
SIGNUP_URL = os.getenv("SIGNUP_URL", "http://game9m.com/h5/#/register?promoCode=79704340")
SIGNAL_LINK = "https://t.me/+uZnBIr3EaN9lNmU1"
CHANNEL_URL = f"https://t.me/{CHANNEL_ID.replace('@', '')}"

# Banner URLs from uploads folder
BASE_UPLOAD_URL = "https://backend.game9mprediction.live/uploads"
DEFAULT_BANNER = f"{BASE_UPLOAD_URL}/banner-5-BNcmeya_.png"
VIP_BANNER = f"{BASE_UPLOAD_URL}/banner-6-Ebe0zEez.png"
REFER_BANNER = f"{BASE_UPLOAD_URL}/refer-banner.png"
OFFER_BANNER = f"{BASE_UPLOAD_URL}/banner-6-Ebe0zEez.png"

def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "game9m"),
            connection_timeout=10
        )
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return None

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

def get_main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎰 রেজিস্ট্রেশন করুন", url=SIGNUP_URL))
    kb.add(InlineKeyboardButton("💎 VIP অ্যাক্সেস পান", callback_data="check_vip"))
    kb.add(InlineKeyboardButton("📊 সিগন্যাল দেখুন", url=SIGNAL_LINK))
    kb.add(InlineKeyboardButton("🎁 রেফারেল স্ট্যাটাস", callback_data="my_referral"))
    return kb

def get_back_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ মূল মেনু", callback_data="back_to_start"))

# ── AUTO-SIGNAL FROM CHANNEL ──────────────────────────────
@bot.channel_post_handler(func=lambda m: m.text)
def handle_channel_post(message):
    text = message.text
    wingo = re.search(r'(Wingo\s+\d+\s+Min)\s*[-:]\s*(Red|Green|Small|Big)\s*\((\d+%)\)', text, re.I)
    aviator = re.search(r'(Aviator)\s*[-:]\s*(\d+\.?\d*x)\s*\((\d+%)\)', text, re.I)
    data = None
    if wingo:
        data = (wingo.group(1), "wingo", "Color Game", wingo.group(2).capitalize(), wingo.group(3), 0)
    elif aviator:
        data = ("Aviator Bot", "aviator", "Next Multiplier", aviator.group(2), aviator.group(3), 0)
    if data:
        db = get_db()
        if db:
            try:
                cur = db.cursor()
                cur.execute("INSERT INTO live_tips (game,category,type,tip,win_rate,`order`) VALUES (%s,%s,%s,%s,%s,%s)", data)
                db.commit()
                print("✅ Signal saved")
            except Exception as e: print("❌ Signal save error:", e)
            finally: cur.close(); db.close()

# ── /start HANDLER ────────────────────────────────────────
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.username
    fname = message.from_user.first_name or "মেম্বার"
    parts = message.text.split()
    payload = parts[1] if len(parts) > 1 else None

    db = get_db()
    if db:
        try:
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT * FROM telegram_users WHERE telegram_id=%s", (uid,))
            existing = cur.fetchone()
            if not existing:
                ref_by = payload.replace("ref_", "") if payload and payload.startswith("ref_") else None
                cur.execute("INSERT INTO telegram_users (telegram_id,username,first_name,referred_by,referral_count) VALUES (%s,%s,%s,%s,0)", (uid, uname, fname, ref_by))
                db.commit()
                if ref_by:
                    cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (ref_by,))
                    ref = cur.fetchone()
                    if ref:
                        nc = (ref["referral_count"] or 0) + 1
                        cur.execute("UPDATE telegram_users SET referral_count=%s WHERE telegram_id=%s", (nc, ref_by))
                        db.commit()
                        try: bot.send_message(ref_by, f"🎉 নতুন রেফারেল! আপনার মোট রেফার: {nc} জন।")
                        except: pass
            else:
                cur.execute("UPDATE telegram_users SET username=%s,first_name=%s WHERE telegram_id=%s", (uname, fname, uid))
                db.commit()
            cur.close(); db.close()
        except: pass

    text = (
        f"👑 *স্বাগতম {fname}! Game9M এর প্রিমিয়াম ড্যাশবোর্ডে আপনাকে অভিনন্দন!* 👑\n\n"
        f"বাংলাদেশের সবচেয়ে ট্রাস্টেড এবং সিকিউর গেমিং প্ল্যাটফর্মে আপনি এখন যুক্ত আছেন। আমাদের প্রতিদিনের নিখুঁত প্রেডিকশন এবং সিগন্যালগুলো মেনে খেলে আপনি নিশ্চিত প্রোফিট করতে পারবেন!\n\n"
        f"⚡ *কেন Game9M সেরা?*\n"
        f"✅ ১০০% সিকিউর ডিপোজিট এবং সুপারফাস্ট ইনস্ট্যান্ট উইথড্র\n"
        f"✅ Wingo ও Aviator গেমের ৯৮% অ্যাকুরেট লাইভ সিগন্যাল\n"
        f"✅ নতুন একাউন্ট খুললেই পাচ্ছেন ৩০০% পর্যন্ত আকর্ষণীয় ওয়েলকাম বোনাস!\n\n"
        f"💰 *উইথড্র নিয়ে চিন্তা?*\n"
        f"আমাদের এখানে পাচ্ছেন বিকাশ, নগদ এবং রকেটের মাধ্যমে অটোমেটিক ও ইনস্ট্যান্ট উইথড্র সুবিধা। জিতুন এবং সাথে সাথেই টাকা নিজের পকেটে নিন!\n\n"
        f"🚀 দেরি না করে আজই আপনার একাউন্ট খুলে খেলা শুরু করুন!\n"
        f"🎯 *বিশেষ অফার:* আপনার বন্ধুদের রেফার করে মোট ১০ জনকে যুক্ত করলেই পাচ্ছেন আমাদের প্রিমিয়াম VIP চ্যানেলের আজীবন ফ্রি অ্যাক্সেস!\n\n"
        f"🌐 [App Link](https://game9m.live)"
    )
    # Sending Image + Buttons for Start
    bot.send_photo(
        message.chat.id, 
        DEFAULT_BANNER, 
        caption=text, 
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ── CALLBACK HANDLERS ─────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    fname = call.from_user.first_name or "মেম্বার"
    
    if call.data == "back_to_start":
        text = (
            f"👑 *স্বাগতম {fname}! মূল মেনু* 👑\n\n"
            f"নিচের বাটনগুলো ব্যবহার করে আপনার কাঙ্ক্ষিত অপশনটি বেছে নিন।"
        )
        try:
            # We edit the caption and photo if possible, or just delete and resend
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(call.message.chat.id, DEFAULT_BANNER, caption=text, reply_markup=get_main_keyboard())
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=get_main_keyboard())

    elif call.data == "check_vip":
        db = get_db()
        rc = 0
        if db:
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (uid,))
            row = cur.fetchone()
            rc = row["referral_count"] if row else 0
            cur.close(); db.close()
        
        bname = bot.get_me().username
        link = f"https://t.me/{bname}?start=ref_{uid}"
        
        if rc >= 10:
            msg = (
                f"🎉 *অভিনন্দন {fname}! আপনি এখন প্রিমিয়াম মেম্বার!* 🎉\n\n"
                f"আপনার ১০টি রেফারেল পূর্ণ হয়েছে। আপনি এখন আমাদের এক্সক্লুসিভ VIP সিগন্যাল গ্রুপের সকল সুবিধা পাবেন।\n\n"
                f"📊 *VIP সুবিধাসমূহ:*\n"
                f"✅ ৯৯% একুরেট Wingo সিগন্যাল\n"
                f"✅ ২৪/৭ পার্সোনাল সাপোর্ট\n\n"
                f"🚀 [সরাসরি VIP গ্রুপে জয়েন করুন]({SIGNAL_LINK})"
            )
        else:
            msg = (
                f"💎 *VIP অ্যাক্সেস ও iPhone 17 জেতার সুযোগ!* 💎\n\n"
                f"সম্মানিত {fname}, আমাদের VIP গ্রুপে জয়েন করে প্রতিদিন ৫,০০০ - ১০,০০০ টাকা পর্যন্ত আয় করার সুযোগ হাতছাড়া করবেন না!\n\n"
                f"📊 *আপনার বর্তমান অগ্রগতি:*\n"
                f"✅ মোট রেফার: `{rc}`/10 জন\n"
                f"🎯 বাকি আছে: `{10-rc}` জন\n\n"
                f"🎁 ১০ জন বন্ধুকে রেফার করলেই পাচ্ছেন আমাদের VIP চ্যানেলের আজীবন ফ্রি অ্যাক্সেস এবং iPhone 17 লাকি ড্র তে অংশগ্রহণের সুযোগ!\n\n"
                f"🔗 *শেয়ার করুন আপনার লিঙ্ক:* `{link}`"
            )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Using banner-6 for VIP/iPhone offer
        bot.send_photo(call.message.chat.id, OFFER_BANNER, caption=msg, reply_markup=get_back_button())

    elif call.data == "my_referral":
        db = get_db()
        rc = 0
        if db:
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (uid,))
            row = cur.fetchone()
            rc = row["referral_count"] if row else 0
            cur.close(); db.close()
            
        bname = bot.get_me().username
        link = f"https://t.me/{bname}?start=ref_{uid}"
        msg = (
            f"🎁 *বন্ধুদের ইনভাইট করুন, আনলিমিটেড বোনাস জিতুন!* 🎁\n\n"
            f"হে {fname}, আপনি কি জানেন? আপনার রেফারেল লিঙ্কের মাধ্যমে যত বেশি বন্ধু যুক্ত হবে, আপনার জয়ের সম্ভাবনা তত বাড়বে!\n\n"
            f"💰 *রেফারেল রিওয়ার্ডস:*\n"
            f"✅ প্রতি সফল রেফারে আকর্ষণীয় বোনাস\n"
            f"✅ ১০ রেফারে আজীবন VIP সিগন্যাল\n"
            f"✅ সাপ্তাহিক টপ রেফারারদের জন্য নগদ পুরস্কার!\n\n"
            f"👥 *আপনার বর্তমান পরিসংখ্যান:*\n"
            f"🏅 মোট সফল রেফার: `{rc}` জন\n\n"
            f"🔗 *আপনার ম্যাজিক লিঙ্ক:* `{link}`\n\n"
            f"বন্ধুদের সাথে লিঙ্কটি শেয়ার করুন এবং আজই ইনকাম শুরু করুন!"
        )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Using refer-banner for Referral page
        bot.send_photo(call.message.chat.id, REFER_BANNER, caption=msg, reply_markup=get_back_button())

# ── DAILY BROADCAST ───────────────────────────────────────
def broadcast():
    db = get_db()
    if db:
        try:
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT `value` FROM settings WHERE `key`='promo_message_format'")
            r = cur.fetchone()
            promo = r["value"] if r and r["value"] else "🎯今日のスペシャルオファー🎯"
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🎰 খেলা শুরু করুন", url=SIGNUP_URL))
            cur.execute("SELECT telegram_id FROM telegram_users")
            users = cur.fetchall()
            cur.close(); db.close()
            for u in users:
                try: bot.send_photo(u["telegram_id"], DEFAULT_BANNER, caption=promo, reply_markup=kb); time.sleep(0.05)
                except: pass
        except: pass

def scheduler():
    schedule.every().day.at("10:00").do(broadcast)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("🤖 Python Bot is starting up with Banner support...")
    db = get_db()
    if db:
        print("✅ DB Connected")
        db.close()
    
    bot.remove_webhook()
    time.sleep(1)
    threading.Thread(target=scheduler, daemon=True).start()
    bot.infinity_polling()
