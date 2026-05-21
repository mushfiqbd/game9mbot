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
SIGNUP_URL = os.getenv("SIGNUP_URL", "https://game9m.live/h5/#/register?invitationCode=34711200196")
SIGNAL_LINK = "https://t.me/+uZnBIr3EaN9lNmU1"
CHANNEL_URL = f"https://t.me/{CHANNEL_ID.replace('@', '')}"

def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "game9m"),
            timeout=10
        )
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        raise e

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

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
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO live_tips (game,category,type,tip,win_rate,`order`) VALUES (%s,%s,%s,%s,%s,%s)", data)
            conn.commit()
            print("✅ Signal saved")
        except Exception as e:
            print("❌ Signal save error:", e)
        finally:
            cur.close(); conn.close()

# ── /start HANDLER ────────────────────────────────────────
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.username
    fname = message.from_user.first_name or "সম্মানিত মেম্বার"
    parts = message.text.split()
    payload = parts[1] if len(parts) > 1 else None

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM telegram_users WHERE telegram_id=%s", (uid,))
        existing = cur.fetchone()

        if not existing:
            ref_by = payload.replace("ref_", "") if payload and payload.startswith("ref_") else None
            cur.execute(
                "INSERT INTO telegram_users (telegram_id,username,first_name,referred_by,referral_count) VALUES (%s,%s,%s,%s,0)",
                (uid, uname, fname, ref_by),
            )
            conn.commit()
            if ref_by:
                cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (ref_by,))
                ref = cur.fetchone()
                if ref:
                    nc = (ref["referral_count"] or 0) + 1
                    cur.execute("UPDATE telegram_users SET referral_count=%s WHERE telegram_id=%s", (nc, ref_by))
                    conn.commit()
                    msg = (
                        f"🎉 *CONGRATULATIONS!* 🎉\n"
                        f"আপনার রেফারেল লিঙ্কে একজন নতুন মেম্বার যুক্ত হয়েছেন!\n\n"
                        f"📊 *বর্তমান রেফারেল স্ট্যাটাস:*\n"
                        f"👥 মোট রেফার: {nc} জন\n"
                        f"🎯 টার্গেট: 10 জন\n"
                    )
                    if nc == 10:
                        msg += (
                            f"\n============================\n"
                            f"✨ *MISSION ACCOMPLISHED!* ✨\n"
                            f"আপনার ১০টি রেফার সফলভাবে সম্পন্ন হয়েছে!\n\n"
                            f"🔓 *VIP CHANNEL UNLOCKED!*\n"
                            f"নিচের লিঙ্কে ক্লিক করে আজীবন ফ্রি লাইভ সিগন্যাল উপভোগ করুন:\n"
                            f"👉 {SIGNAL_LINK}\n"
                            f"============================"
                        )
                    try: bot.send_message(ref_by, msg)
                    except: pass
        else:
            cur.execute("UPDATE telegram_users SET username=%s,first_name=%s WHERE telegram_id=%s", (uname, fname, uid))
            conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print("DB Error:", e)

    # Build response
    text = (
        f"👑 *স্বাগতম {fname}! Game9M এর প্রিমিয়াম ড্যাশবোর্ডে আপনাকে অভিনন্দন!* 👑\n\n"
        f"বাংলাদেশের সবচেয়ে ট্রাস্টেড এবং সিকিউর গেমিং প্ল্যাটফর্মে আপনি এখন যুক্ত আছেন। "
        f"আমাদের প্রতিদিনের নিখুঁত প্রেডিকশন এবং সিগন্যালগুলো মেনে খেলে আপনি নিশ্চিত প্রোফিট করতে পারবেন!\n\n"
        f"⚡ *কেন Game9M সেরা?*\n"
        f"✅ *১০০% সিকিউর ডিপোজিট এবং ৫ মিনিটে সুপারফাস্ট উইথড্র*\n"
        f"✅ *Wingo ও Aviator গেমের ৯৮% অ্যাকুরেট লাইভ সিগন্যাল*\n"
        f"✅ *নতুন একাউন্ট খুললেই পাচ্ছেন ৩০০% পর্যন্ত আকর্ষণীয় ওয়েলকাম বোনাস!*\n\n"
        f"🚀 *দেরি না করে আজই আপনার একাউন্ট খুলে খেলা শুরু করুন!*\n"
        f"🎯 *বিশেষ অফার:* আপনার বন্ধুদের রেফার করে মোট ১০ জনকে যুক্ত করলেই পাচ্ছেন আমাদের প্রিমিয়াম VIP চ্যানেলের আজীবন ফ্রি অ্যাক্সেস!"
    )
    kb = InlineKeyboardMarkup(row_width=1)

    if payload == "channel":
        text = (
            f"✅ *সম্মানিত মেম্বার {fname}, আপনার চ্যানেল অ্যাক্সেস প্রস্তুত!* ✅\n\n"
            f"Game9M এর অফিশিয়াল ফ্রি সিগন্যাল চ্যানেল এখন আপনার জন্য উন্মুক্ত। "
            f"প্রতিদিনের ফ্রী সিগন্যালগুলো মিস না করতে এখনই নিচের বাটন থেকে জয়েন করে নিন!"
        )
        kb.add(InlineKeyboardButton("📢 অফিশিয়াল সিগন্যাল চ্যানেলে জয়েন করুন", url=CHANNEL_URL))
    elif payload == "vip":
        text = (
            f"💎 *অসাধারণ {fname}! আপনি একজন VIP মেম্বার!* 💎\n\n"
            f"আমাদের এক্সক্লুসিভ VIP সার্কেলে আপনাকে স্বাগতম। আপনি এখন থেকে পাবেন সর্বোচ্চ অ্যাকুরেসি সম্পন্ন স্পেশাল সিগন্যাল!"
        )
        kb.add(InlineKeyboardButton("🚀 VIP প্রেডিকশন গ্রুপে প্রবেশ করুন", url=SIGNAL_LINK))

    kb.add(InlineKeyboardButton("🎰 রেজিস্ট্রেশন করুন", url=SIGNUP_URL))
    kb.add(InlineKeyboardButton("💎 VIP অ্যাক্সেস পান", callback_data="check_vip"))
    kb.add(InlineKeyboardButton("📊 সিগন্যাল দেখুন", url=SIGNAL_LINK))
    kb.add(InlineKeyboardButton("🎁 রেফারেল স্ট্যাটাস", callback_data="my_referral"))
    bot.reply_to(message, text, reply_markup=kb)

# ── VIP ACCESS CHECK ──────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "check_vip")
def check_vip(call):
    uid = str(call.from_user.id)
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        rc = row["referral_count"] if row else 0
        
        bname = bot.get_me().username
        link = f"https://t.me/{bname}?start=ref_{uid}"

        if rc >= 10:
            msg = (
                f"🎉 *অভিনন্দন! আপনার ১০টি রেফার পূর্ণ হয়েছে!* 🎉\n\n"
                f"আপনি এখন আমাদের প্রিমিয়াম VIP সিগন্যাল গ্রুপের জন্য যোগ্য।\n"
                f"নিচের লিঙ্কে ক্লিক করে এখনই জয়েন করুন:\n\n"
                f"👉 {SIGNAL_LINK}\n\n"
                f"সাথেই থাকুন, Game9M এর সাথেই জিতুন! 🚀"
            )
            bot.send_message(call.message.chat.id, msg)
        else:
            msg = (
                f"❌ *দুঃখিত! আপনার এখনও ১০ জন রেফার পূর্ণ হয়নি।* ❌\n\n"
                f"📊 আপনার বর্তমান রেফার: `{rc}` জন।\n"
                f"🎯 টার্গেট: `10` জন।\n"
                f"বাকি আছে: `{10-rc}` জন।\n\n"
                f"VIP চ্যানেলের অ্যাক্সেস পেতে নিচের ইনভাইটেশন লিঙ্কটি বন্ধুদের সাথে শেয়ার করুন:\n"
                f"🔗 `{link}`"
            )
            bot.send_message(call.message.chat.id, msg)
        
        cur.close(); conn.close()
    except Exception as e:
        print(e)
        bot.send_message(call.message.chat.id, "তথ্য চেক করতে সমস্যা হচ্ছে। কিছুক্ষণ পর আবার চেষ্টা করুন।")

# ── REFERRAL STATUS ───────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_referral")
def referral(call):
    bot.answer_callback_query(call.id)
    uid = str(call.from_user.id)
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT referral_count FROM telegram_users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        rc = row["referral_count"] if row else 0
        bname = bot.get_me().username
        link = f"https://t.me/{bname}?start=ref_{uid}"
        if rc >= 10:
            msg = (
                f"🎁 *আপনার স্পেশাল রেফারেল ড্যাশবোর্ড* 🎁\n\n"
                f"👤 *আপনার প্রোফাইল স্ট্যাটাস: VIP মেম্বার 💎*\n"
                f"👥 *মোট রেফারেল:* {rc} / 10 জন\n\n"
                f"🌟 *অভিনন্দন! আপনার VIP অ্যাক্সেস আনলক করা হয়েছে!*\n"
                f"নিচের লিঙ্ক থেকে স্পেশাল VIP সিগন্যাল গ্রুপে যুক্ত হন:\n"
                f"👉 {SIGNAL_LINK}\n\n"
                f"🔗 *আপনার ইনভাইটেশন লিংক (আরো বন্ধুদের জন্য):*\n`{link}`"
            )
        else:
            msg = (
                f"🎁 *আপনার রেফারেল ড্যাশবোর্ড* 🎁\n\n"
                f"👥 *আপনি এ পর্যন্ত রেফার করেছেন:* {rc} জন\n"
                f"🎯 *VIP আনলক করতে আর প্রয়োজন:* {10-rc} জন!\n\n"
                f"🚀 *কীভাবে কাজ করবেন?*\n"
                f"নিচের স্পেশাল লিঙ্কটি কপি করে আপনার বন্ধুদের সাথে শেয়ার করুন। "
                f"যখনই ১০ জন এই লিঙ্কে ক্লিক করে এই বটে যুক্ত হবে, "
                f"তখনই আপনার কাছে সিক্রেট VIP গ্রুপের লিংক চলে আসবে!\n\n"
                f"🔗 *আপনার স্পেশাল ইনভাইটেশন লিংক:* (এটি কপি করে শেয়ার করুন)\n`{link}`"
            )
        bot.send_message(call.message.chat.id, msg)
        cur.close(); conn.close()
    except Exception as e:
        print(e)
        bot.send_message(call.message.chat.id, "ডেটা আনতে সমস্যা হচ্ছে।")

# ── DAILY BROADCAST ───────────────────────────────────────
def broadcast():
    print("📢 Daily Broadcast...")
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT `value` FROM settings WHERE `key`='promo_message_format'")
        r = cur.fetchone()
        promo = r["value"] if r and r["value"] else (
            "🎯 𝗝𝗔𝗖𝗞𝗣𝗢𝗧 𝗔𝗟𝗘𝗥𝗧! 𝗪𝗜𝗡 𝗕𝗜𝗚 𝗧𝗢𝗗𝗔𝗬! 🎯\n\n"
            "🔥 *Game9M এর মেগা অফারে আপনাকে স্বাগতম!* 🔥\n\n"
            "আপনি কি জানেন আজ Game9M দিচ্ছে সবচেয়ে বেশি প্রফিট করার অসাধারণ সুযোগ? \n"
            "আমাদের ৯৮% অ্যাকুরেট লাইভ সিগন্যাল ফলো করে প্রতিদিন হাজার হাজার মেম্বার লাখ টাকা ইনকাম করছে!\n\n"
            "✨ *কেন আজই আপনার খেলা শুরু করা উচিত?*\n"
            "💵 ১০০% সিকিউর ডিপোজিট ও সুপারফাস্ট ৫ মিনিটে উইথড্র!\n"
            "🎁 নতুন রেজিস্ট্রেশনে ৩০০% পর্যন্ত আকর্ষণীয় ইনস্ট্যান্ট বোনাস!\n"
            "📈 Wingo, Aviator এবং Crazy Time এর এক্সক্লুসিভ লাইভ প্রেডিকশন!\n\n"
            "🚀 দেরি না করে এখনই নিচের লিঙ্কে ক্লিক করে একাউন্ট খুলুন এবং জয়েন করুন আমাদের লাইভ সিগন্যাল চ্যানেলে!"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎰 খেলা শুরু করুন", url=SIGNUP_URL))
        kb.add(InlineKeyboardButton("📊 লাইভ সিগন্যাল", url=SIGNAL_LINK))
        cur.execute("SELECT telegram_id FROM telegram_users")
        for u in cur.fetchall():
            try:
                bot.send_message(u["telegram_id"], promo, reply_markup=kb)
                time.sleep(0.1)
            except: pass
        cur.close(); conn.close()
    except Exception as e:
        print("Broadcast error:", e)

def scheduler():
    schedule.every().day.at("10:00").do(broadcast)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing in .env!")
        exit(1)
    print("🤖 Python Bot is starting up in Polling format...")
    
    # Remove webhook to avoid Telegram 409 Conflict error
    bot.remove_webhook()
    time.sleep(1)
    
    # Start Scheduler
    threading.Thread(target=scheduler, daemon=True).start()
    bot.infinity_polling()
