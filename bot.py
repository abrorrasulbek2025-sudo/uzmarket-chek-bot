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
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

# ======================
# CONFIG
# ======================

ADMIN_ID = 6056893338
TOKEN = os.getenv("BOT_TOKEN")

if TOKEN is None:
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
# PRICE + PDF
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
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # LOGO
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=2 * inch, height=1 * inch)
        elements.append(logo)

    elements.append(Spacer(1, 20))

    # TITLE
    elements.append(Paragraph("<b>UZMARKET OPTOM CHEK</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    data = [
        ["Mahsulot", product],
        ["Miqdor", str(qty)],
        ["Narx (dona)", f"{price:,} so'm"],
        ["JAMI", f"{total:,} so'm"],
        ["Sana", now],
    ]

    table = Table(data, colWidths=[220, 250])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 3), (-1, 3), colors.lightgrey),  # JAMI qatori
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 40))

    # IMZO
    if os.path.exists("signature.png"):
        elements.append(Paragraph("Mas'ul shaxs imzosi:", styles["Normal"]))
        elements.append(Spacer(1, 10))
        signature = Image("signature.png", width=2 * inch, height=1 * inch)
        elements.append(signature)

    elements.append(Spacer(1, 20))

    # SHTAMP
    if os.path.exists("stamp.png"):
        elements.append(Paragraph("Korxona muhri:", styles["Normal"]))
        elements.append(Spacer(1, 10))
        stamp = Image("stamp.png", width=2 * inch, height=2 * inch)
        elements.append(stamp)

    doc.build(elements)

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
