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
    blue = colors.HexColor("#1f4e8c")

    y = height - 60

    # LOGO
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", width/2 - 100, y - 60, width=200, height=60, mask='auto')
    y -= 80

    # Title
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(blue)
    c.drawCentredString(width/2, y, "UZMARKET OPTOM CHEK")
    y -= 20

    c.setStrokeColor(blue)
    c.line(60, y, width - 60, y)
    y -= 30

    # Chek info
    c.setFont("Helvetica", 11)
    c.setFillColor(blue)

    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    c.drawString(60, y, "Sotuvchi: UzMarketOptom")
    c.drawRightString(width - 60, y, f"Chek № {chek_no}")
    y -= 18

    c.drawString(60, y, "Manzil: Samarqand sh.")
    c.drawRightString(width - 60, y, f"Sana: {today}")
    y -= 18

    c.drawString(60, y, "Tel: +998 XX XXX XX XX")
    y -= 25

    c.line(60, y, width - 60, y)
    y -= 25

    # Table Header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "№")
    c.drawString(100, y, "Mahsulot")
    c.drawString(350, y, "Miqdor")
    c.drawString(420, y, "Narx")
    c.drawString(480, y, "Summa")
    y -= 15

    c.line(60, y, width - 60, y)
    y -= 20

    # Items
    c.setFont("Helvetica", 11)
    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        c.drawString(60, y, str(i))
        c.drawString(100, y, item["product"])
        c.drawRightString(390, y, str(item["qty"]))
        c.drawRightString(460, y, f"{item['price']:,}")
        c.drawRightString(width - 60, y, f"{item['total']:,}")
        total_sum += item["total"]
        y -= 18

    y -= 10
    c.line(300, y, width - 60, y)
    y -= 25

    # JAMI
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(blue)
    c.drawRightString(width - 60, y, f"JAMI: {total_sum:,} so'm")

    # Stamp bottom left
    if os.path.exists("stamp.png"):
        c.drawImage("stamp.png", 60, 80, width=180, height=180, mask='auto')

    # Signature bottom right
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 240, 100, width=180, height=70, mask='auto')

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
