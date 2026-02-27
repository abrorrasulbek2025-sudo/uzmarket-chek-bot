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
LIGHT_LINE = colors.HexColor("#d9e2f3")

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

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_product"] = update.message.text
    await update.message.reply_text("Miqdorini kiriting:")
    return QTY

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["current_qty"] = int(update.message.text)
    except:
        await update.message.reply_text("Iltimos son kiriting.")
        return QTY

    await update.message.reply_text("Narxini kiriting:")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
    except:
        await update.message.reply_text("Iltimos son kiriting.")
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

async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() in ["ha", "yes"]:
        await update.message.reply_text("Mahsulot nomini kiriting:")
        return PRODUCT
    else:
        return await generate_pdf(update, context)

# ======================
# PREMIUM PDF
# ======================

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = "chek.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    y = height - 100

    # ===== LOGO =====
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", width/2 - 110, y, width=220, height=90, mask='auto')

    y -= 20

    # ===== LINE =====
    c.setStrokeColor(BRAND_BLUE)
    c.setLineWidth(1.5)
    c.line(60, y, width - 60, y)

    y -= 40

    # ===== INFO BLOCK =====
    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_BLUE)

    # Left
    c.drawString(60, y + 15, "Sotuvchi: UzMarketOptom")
    c.drawString(60, y, "Manzil: Samarqand sh.")
    c.drawString(60, y - 15, "Tel: +998 97 446 72 82")
    c.drawString(60, y - 15, "Tel: +998 94 754 49 30")
    
    # Right
    c.drawRightString(width - 60, y + 15, f"Chek № {chek_no}")
    c.drawRightString(width - 60, y, f"Sana: {today}")

    y -= 60

    # ===== TABLE =====
    table_left = 60
    table_right = width - 60
    row_height = 28

    col_no = table_left + 10
    col_product = table_left + 50
    col_qty = table_left + 360
    col_price = table_left + 440
    col_total = table_right - 10

    # Header text
    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_no, y, "№")
    c.drawString(col_product, y, "Mahsulot")
    c.drawRightString(col_qty, y, "Miqdor")
    c.drawRightString(col_price, y, "Narx")
    c.drawRightString(col_total, y, "Summa")

    y -= 10
    c.setStrokeColor(LIGHT_LINE)
    c.line(table_left, y, table_right, y)

    total_sum = 0
    c.setFont("Helvetica", 11)
    c.setStrokeColor(LIGHT_LINE)

    for i, item in enumerate(context.user_data["items"], start=1):
        y -= row_height

        c.drawString(col_no, y + 8, str(i))
        c.drawString(col_product, y + 8, item["product"])
        c.drawRightString(col_qty, y + 8, str(item["qty"]))
        c.drawRightString(col_price, y + 8, f"{item['price']:,}")
        c.drawRightString(col_total, y + 8, f"{item['total']:,}")

        c.line(table_left, y, table_right, y)

        total_sum += item["total"]

    # ===== TOTAL =====
    y -= 40
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(BRAND_BLUE)
    c.drawRightString(table_right, y, f"JAMI: {total_sum:,} so'm")

    c.setLineWidth(1.5)
    c.line(table_right - 220, y - 5, table_right, y - 5)

    # ===== STAMP =====
    if os.path.exists("stamp.png"):
        c.drawImage("stamp.png", 60, 90, width=180, height=180, mask='auto')

    # ===== SIGNATURE =====
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 250, 120, width=180, height=70, mask='auto')

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
