import logging
import requests
import random
import string
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Konfigurasi ===
BOT_TOKEN = ""  # Ganti dengan token bot kamu
BASE_URL = "https://api.mail.tm"
MAX_RETRIES = 3

# === Logging (Opsional) ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === Fungsi Pendukung ===
def get_domains():
    response = requests.get(f"{BASE_URL}/domains")
    response.raise_for_status()
    domains = response.json()["hydra:member"]
    return [d["domain"] for d in domains]

def generate_username(prefix):
    random_number = ''.join(random.choices(string.digits, k=5))
    return f"{prefix}{random_number}"

def create_account(email, password):
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password})

        if response.status_code == 201:
            return True
        elif response.status_code == 422:
            return False  # Sudah dipakai
        else:
            time.sleep(2)
    return False

def save_to_file(email, password):
    waktu_buat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("list.txt", "a", encoding="utf-8") as f:
        f.write(f"{email} | {password} | {waktu_buat}\n")
    with open("listemail.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}\n")

# === Handler Bot ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Gunakan perintah:\n"
        "/buatemail [prefix]|[password] [jumlah]\n"
        "Contoh: /buatemail jijin|ganteng 5"
    )

async def buatemail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2 or "|" not in args[0] or not args[1].isdigit():
        await update.message.reply_text(
            "⚠️ Format salah!\nGunakan: /buatemail prefix|password jumlah\n"
            "Contoh: /buatemail jijin|ganteng 5"
        )
        return

    prefix_pass = args[0].split("|", 1)
    if len(prefix_pass) != 2:
        await update.message.reply_text("⚠️ Prefix dan password tidak valid. Gunakan tanda | sebagai pemisah.")
        return

    prefix, password = prefix_pass
    jumlah = int(args[1])

    await update.message.reply_text(f"🚀 Membuat {jumlah} email dengan prefix '{prefix}' dan password '{password}'...")

    try:
        domains = get_domains()
        chosen_domain = next((d for d in domains if "indigobook.com" in d), domains[0])
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengambil domain: {e}")
        return

    created = []

    for i in range(jumlah):
        username = generate_username(prefix)
        email = f"{username}@{chosen_domain}"
        success = create_account(email, password)

        if success:
            save_to_file(email, password)
            created.append(f"{email} | {password}")
        time.sleep(1)

    if created:
        message = "✅ Selesai!\nBerhasil dibuat:\n" + "\n".join(created) + "\n\nLogin di https://mail.tm"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("❌ Tidak ada email yang berhasil dibuat.")

# === Setup Bot ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buatemail", buatemail))

    print("🤖 Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
