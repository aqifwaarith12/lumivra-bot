import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# 1. WEB SERVER (UNTUK JALANKAN BOT 24/7)
# ============================================================
app = Flask('')

@app.route('/')
def home():
    return "Bot QnA Lumivra sedang aktif!"

def run():
    # Menggunakan port 8080 yang biasanya standard untuk cloud hosting
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ============================================================
# 2. KONFIGURASI BOT & ID GROUP
# ============================================================
TOKEN = "8462553126:AAE_97YmoGv-3onuMoQOqjP_dBSNqcv5Vfc"

user_state = {}
message_map = {}

# Senarai ID Group terbaru yang anda berikan
SUBJECT_GROUP = {
    "Matematik": -1003922249943,
    "Biologi": -1003974897635,
    "Kimia": -1003925639791,
    "Fizik": -1003935386679,
    "Bahasa Melayu": -1003729496213,
    "Bahasa Inggeris": -1003737811379,
    "Bahasa Arab": -1003567653678,
    "Bahasa Jepun": -1003950347219,
    "Geografi": -1003901040452,
    "Pendidikan Islam": -1003903720010,
    "Sejarah": -1003991109927,
    "PJPK": -1003988466929,
    "Pendidikan Seni": -1003996331974,
    "Sains Kejuruteraan": -1003977885252,
    "Reka Bentuk Teknologi": -1003987023976,
}

DEPARTMENTS = {
    "Matematik": ["Matematik"],
    "Bahasa": ["Bahasa Melayu", "Bahasa Inggeris", "Bahasa Jepun", "Bahasa Arab"],
    "Sains": ["Biologi", "Kimia", "Fizik"],
    "Sains Sosial": ["Geografi", "Pendidikan Islam", "Sejarah", "PJPK", "Pendidikan Seni"],
    "Teknikal": ["Sains Kejuruteraan", "Reka Bentuk Teknologi"]
}

ALL_SUBJECTS = [s for sublist in DEPARTMENTS.values() for s in sublist]

# ============================================================
# 3. FUNGSI-FUNGSI BOT
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_state[user_id] = {} 
    keyboard = [[d] for d in DEPARTMENTS.keys()]
    await update.message.reply_text(
        "📚 **QnA Akademik Lumivra**\nSila pilih Jabatan anda:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.chat_id

    # Fungsi Kembali
    if text == "⬅️ Kembali ke Jabatan":
        user_state[user_id] = {}
        keyboard = [[d] for d in DEPARTMENTS.keys()]
        await update.message.reply_text(
            "📚 Pilih Jabatan semula:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # Pemilihan Subjek
    if text in ALL_SUBJECTS:
        user_state[user_id] = {"subject": text}
        keyboard = [["⬅️ Kembali ke Jabatan"]]
        await update.message.reply_text(
            f"✏️ Subjek **{text}** dipilih.\n\nSila taip soalan atau hantar **gambar** soalan tersebut:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # Pemilihan Jabatan
    if text in DEPARTMENTS:
        user_state[user_id] = {"department": text}
        keyboard = [[s] for s in DEPARTMENTS[text]]
        keyboard.append(["⬅️ Kembali ke Jabatan"])
        await update.message.reply_text(
            f"📖 Jabatan {text} dipilih. Sila pilih Subjek:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # Proses Hantar Soalan (Teks atau Gambar)
    if user_id in user_state and "subject" in user_state[user_id]:
        subject = user_state[user_id]["subject"]
        group_id = SUBJECT_GROUP.get(subject)

        user_name = update.message.from_user.first_name
        soalan_teks = text if text else update.message.caption or "[Gambar]"
        
        caption_msg = (
            f"📩 **SOALAN BARU**\n\n👤 Dari: {user_name}\n📚 Subjek: {subject}\n\n❓ Soalan: {soalan_teks}\n\n👉 **Reply** mesej ini untuk memberi jawapan."
        )

        try:
            if update.message.photo:
                photo_id = update.message.photo[-1].file_id
                sent = await context.bot.send_photo(chat_id=group_id, photo=photo_id, caption=caption_msg)
            else:
                sent = await context.bot.send_message(chat_id=group_id, text=caption_msg)

            message_map[sent.message_id] = user_id
            
            await update.message.reply_text(
                "✅ Soalan telah dihantar! Tunggu jawapan daripada cikgu.\n\nKlik /start untuk tanya soalan baru.",
                reply_markup=ReplyKeyboardRemove()
            )
            del user_state[user_id] 
            
        except Exception as e:
            await update.message.reply_text(f"❌ Gagal hantar ke group.\nError: {e}")

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cikgu reply di group untuk dihantar balik kepada pelajar"""
    if not update.message.reply_to_message:
        return

    replied_id = update.message.reply_to_message.message_id

    if replied_id in message_map:
        student_id = message_map[replied_id]
        jawapan = update.message.text or "[Gambar/Media]"
        
        try:
            await context.bot.send_message(
                chat_id=student_id,
                text=f"📢 **JAWAPAN DARI CIKGU:**\n\n{jawapan}\n\n---\nKlik /start untuk tanya soalan baru."
            )
            await update.message.reply_text("✅ Jawapan dihantar kepada pelajar.")
        except:
            await update.message.reply_text("❌ Gagal hantar (Pelajar block bot).")

# ============================================================
# 4. PELAKSANAAN UTAMA
# ============================================================
def main():
    # Menjalankan web server di latar belakang
    keep_alive()
    
    print("Bot QnA Lumivra sedang berjalan...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Susunan handler
    app.add_handler(MessageHandler(filters.REPLY, handle_reply))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
