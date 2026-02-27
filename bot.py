import os
import datetime
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ======================
# CONFIG
# ======================

ADMIN_ID = 6056893338
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi.")

PRODUCT, QTY, PRICE, ADD_MORE = range(4)

BRAND_BLUE = colors.HexColor("#1f4e8c")
LIGHT_BLUE = colors.HexColor("#2d67b2")

# ======================
# START
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return ConversationHandler.END

    context.user_data["items"] = []
    await update.message.reply_text("Mahsulot nomini kiriting:")
    return PRODUCT

# ======================
# PRODUCT
# ======================

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_product"] = update.message.text
    await update.message.reply_text("Miqdorini kiriting:")
    return QTY

# ======================
# QTY
# ======================

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["current_qty"] = int(update.message.text)
    except:
        await update.message.reply_text("Son kiriting.")
        return QTY

    await update.message.reply_text("Narxini kiriting:")
    return PRICE

# ======================
# PRICE
# ======================

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
    except:
        await update.message.reply_text("Son kiriting.")
        return PRICE

    item = {
        "product": context.user_data["current_product"],
        "qty": context.user_data["current_qty"],
        "price": price,
        "total": context.user_data["current_qty"] * price
    }

    context.user_data["items"].append(item)

    await update.message.reply_text("Yana mahsulot qo‘shasizmi? (ha/yo‘q)")
    return ADD_MORE

# ======================
# ADD MORE
# ======================

async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() in ["ha", "yes"]:
        await update.message.reply_text("Mahsulot nomini kiriting:")
        return PRODUCT
    else:
        return await generate_pdf(update, context)

# ======================
# PDF GENERATION
# ======================

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = "chek.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    width, height = A4

    # ===== HEADER BLOCK =====
    c.setFillColor(BRAND_BLUE)
    c.rect(0, height - 120, width, 120, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 70, "UZMARKET OPTOM CHEK")

    # ===== CHEK INFO BLOCK =====
    c.setFont("Helvetica-Bold", 12)
    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    c.drawRightString(width - 60, height - 100, f"Chek № {chek_no}")
    c.drawRightString(width - 60, height - 115, f"Sana: {today}")

    # ===== SELLER INFO =====
    y = height - 150
    c.setFillColor(BRAND_BLUE)
    c.setFont("Helvetica", 12)
    c.drawString(60, y, "Sotuvchi: UzMarketOptom")
    y -= 18
    c.drawString(60, y, "Manzil: Samarqand sh.")
    y -= 18
    c.drawString(60, y, "Tel: +998 XX XXX XX XX")
    y -= 30

    # ===== TABLE HEADER =====
    c.setFillColor(LIGHT_BLUE)
    c.rect(60, y, width - 120, 25, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(65, y + 7, "№")
    c.drawString(100, y + 7, "Mahsulot")
    c.drawString(360, y + 7, "Miqdor")
    c.drawString(430, y + 7, "Narx")
    c.drawString(490, y + 7, "Summa")

    y -= 25

    # ===== ITEMS =====
    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_BLUE)

    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        y -= 22
        c.drawString(65, y, str(i))
        c.drawString(100, y, item["product"])
        c.drawRightString(400, y, str(item["qty"]))
        c.drawRightString(470, y, f"{item['price']:,}")
        c.drawRightString(width - 60, y, f"{item['total']:,}")
        total_sum += item["total"]

    # ===== TOTAL =====
    y -= 40
    c.setStrokeColor(BRAND_BLUE)
    c.line(width - 250, y + 20, width - 60, y + 20)

    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - 60, y, f"JAMI: {total_sum:,} so'm")

    # ===== STAMP =====
    if os.path.exists("stamp.png"):
        c.drawImage("stamp.png", 60, 80, width=180, height=180, mask='auto')

    # ===== SIGNATURE =====
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 250, 110, width=180, height=70, mask='auto')

    c.save()

    with open(file_name, "rb") as f:
        await update.message.reply_document(f)

    return ConversationHandler.END

# ======================
# CANCEL
# ======================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

# ======================
# MAIN
# ======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product)],
            QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
