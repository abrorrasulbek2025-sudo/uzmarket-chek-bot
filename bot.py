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
# PDF GENERATION (PREMIUM GRID)
# ======================

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = "chek.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    y = height - 120

    # ===== LOGO =====
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", width/2 - 120, y, width=240, height=100, mask='auto')

    y -= 20

    # ===== BLUE LINE =====
    c.setStrokeColor(BRAND_BLUE)
    c.setLineWidth(2)
    c.line(60, y, width - 60, y)

    y -= 40

    # ===== INFO BLOCK =====
    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    c.setFont("Helvetica", 12)
    c.setFillColor(BRAND_BLUE)

    c.drawString(60, y + 20, "Sotuvchi: UzMarketOptom")
    c.drawString(60, y + 5, "Manzil: Samarqand sh.")
    c.drawString(60, y - 10, "Tel: +998 XX XXX XX XX")

    c.drawRightString(width - 60, y + 20, f"Chek № {chek_no}")
    c.drawRightString(width - 60, y + 5, f"Sana: {today}")

    y -= 50

    # ===== TABLE HEADER =====
    table_left = 60
    table_right = width - 60
    row_height = 28

    columns = [60, 100, 370, 430, 500, table_right]

    c.setFillColor(LIGHT_BLUE)
    c.rect(table_left, y, table_right - table_left, row_height, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)

    c.drawString(columns[0] + 5, y + 8, "№")
    c.drawString(columns[1] + 5, y + 8, "Mahsulot")
    c.drawRightString(columns[3] - 5, y + 8, "Miqdor")
    c.drawRightString(columns[4] - 5, y + 8, "Narx")
    c.drawRightString(columns[5] - 5, y + 8, "Summa")

    # Vertical lines header
    c.setStrokeColor(colors.white)
    for col in columns[1:-1]:
        c.line(col, y, col, y + row_height)

    y -= row_height

    # ===== ITEMS =====
    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_BLUE)
    c.setStrokeColor(BRAND_BLUE)

    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        c.rect(table_left, y, table_right - table_left, row_height, fill=0)

        # Vertical lines
        for col in columns[1:-1]:
            c.line(col, y, col, y + row_height)

        c.drawString(columns[0] + 5, y + 8, str(i))
        c.drawString(columns[1] + 5, y + 8, item["product"])
        c.drawRightString(columns[3] - 5, y + 8, str(item["qty"]))
        c.drawRightString(columns[4] - 5, y + 8, f"{item['price']:,}")
        c.drawRightString(columns[5] - 5, y + 8, f"{item['total']:,}")

        total_sum += item["total"]
        y -= row_height

    # ===== TOTAL =====
    y -= 20
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(table_right, y, f"JAMI: {total_sum:,} so'm")

    c.setLineWidth(1.5)
    c.line(table_right - 200, y - 5, table_right, y - 5)

    # ===== STAMP =====
    if os.path.exists("stamp.png"):
        c.drawImage("stamp.png", 60, 90, width=180, height=180, mask='auto')

    # ===== SIGNATURE =====
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 250, 130, width=180, height=70, mask='auto')

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
