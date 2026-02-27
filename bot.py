import os
import datetime
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

PRODUCT, QTY, PRICE = range(3)

# ======================
# START
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return ConversationHandler.END

    await update.message.reply_text("Mahsulot nomini kiriting:")
    return PRODUCT

# ======================
# PRODUCT
# ======================

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product"] = update.message.text
    await update.message.reply_text("Miqdorini kiriting:")
    return QTY

# ======================
# QTY
# ======================

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["qty"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, son kiriting.")
        return QTY

    await update.message.reply_text("Narxini kiriting:")
    return PRICE

# ======================
# PRICE (PREMIUM PDF)
# ======================

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["price"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, son kiriting.")
        return PRICE

    product = context.user_data["product"]
    qty = context.user_data["qty"]
    price = context.user_data["price"]
    total = qty * price

    file_name = "chek.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    width, height = A4
    y = height - 80

    # LOGO
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", width/2 - 80, y, width=160, height=70, mask='auto')
    y -= 90

    # TITLE
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, y, "UZMARKET OPTOM CHEK")
    y -= 25

    # Divider
    c.setStrokeColor(colors.grey)
    c.line(80, y, width - 80, y)
    y -= 40

    # Body
    c.setFont("Helvetica", 13)

    c.drawString(100, y, "Mahsulot:")
    c.drawRightString(width - 100, y, product)
    y -= 30

    c.drawString(100, y, "Miqdor:")
    c.drawRightString(width - 100, y, str(qty))
    y -= 30

    c.drawString(100, y, "Narx (dona):")
    c.drawRightString(width - 100, y, f"{price:,} so'm")
    y -= 30

    # Divider
    c.setStrokeColor(colors.black)
    c.line(100, y, width - 100, y)
    y -= 35

    # JAMI
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.darkred)
    c.drawString(100, y, "JAMI:")
    c.drawRightString(width - 100, y, f"{total:,} so'm")
    c.setFillColor(colors.black)
    y -= 50

    # Date
    c.setFont("Helvetica", 11)
    c.drawRightString(width - 80, y,
        datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))
    y -= 40

    # Watermark stamp (semi transparent)
    if os.path.exists("stamp.png"):
        c.saveState()
        c.setFillAlpha(0.15)
        c.drawImage(
            "stamp.png",
            width/2 - 120,
            height/2 - 120,
            width=240,
            height=240,
            mask='auto'
        )
        c.restoreState()

    # Signature
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", 100, 150, width=140, height=60, mask='auto')

    # Footer
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width/2, 100, "Rahmat xaridingiz uchun!")

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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
