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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# =====================
# CONFIG
# =====================

ADMIN_ID = 6056893338
TOKEN = os.getenv("BOT_TOKEN")

PRODUCT, QTY, PRICE = range(3)

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return ConversationHandler.END

    await update.message.reply_text("Mahsulot nomini kiriting:")
    return PRODUCT

# =====================
# STEP 1
# =====================

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product"] = update.message.text
    await update.message.reply_text("Miqdorini kiriting:")
    return QTY

# =====================
# STEP 2
# =====================

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["qty"] = update.message.text
    await update.message.reply_text("Narxini kiriting:")
    return PRICE

# =====================
# STEP 3 + PDF
# =====================

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text

    file_name = "check.pdf"
    doc = SimpleDocTemplate(file_name)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("UZMARKET CHEK", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Mahsulot", context.user_data["product"]],
        ["Miqdor", context.user_data["qty"]],
        ["Narx", context.user_data["price"]],
        ["Sana", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]

    table = Table(data, colWidths=[2.5 * inch, 3 * inch])
    table.setStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ])

    elements.append(table)

    doc.build(elements)

    await update.message.reply_document(document=open(file_name, "rb"))
    return ConversationHandler.END

# =====================
# CANCEL
# =====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

# =====================
# MAIN
# =====================

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
