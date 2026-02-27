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

ADMIN_ID = 6056893338
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi.")

PRODUCT, QTY, PRICE, ADD_MORE = range(4)

BRAND_BLUE = colors.HexColor("#1f4e8c")

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

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = "chek.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    y = height - 100

    # LOGO
    if os.path.exists("logo.png"):
        c.drawImage("logo.png", width/2 - 110, y, width=220, height=90, mask='auto')

    y -= 20

    # TOP LINE
    c.setStrokeColor(BRAND_BLUE)
    c.setLineWidth(1.5)
    c.line(60, y, width - 60, y)

    y -= 40

    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    c.setFont("Helvetica", 11)
    c.setFillColor(BRAND_BLUE)

    c.drawString(60, y + 15, "Sotuvchi: UzMarketOptom")
    c.drawString(60, y, "Manzil: Samarqand sh.")
    c.drawString(60, y - 15, "Tel: +998 XX XXX XX XX")

    c.drawRightString(width - 60, y + 15, f"Chek № {chek_no}")
    c.drawRightString(width - 60, y, f"Sana: {today}")

    y -= 60

    # TABLE STRUCTURE
    table_left = 60
    table_right = width - 60
    row_height = 28

    col_positions = [
        table_left,
        table_left + 40,
        table_left + 350,
        table_left + 430,
        table_right
    ]

    # HEADER BORDER
    c.rect(table_left, y - row_height, table_right - table_left, row_height, stroke=1, fill=0)

    # HEADER TEXT
    c.setFont("Helvetica-Bold", 11)
    c.drawString(col_positions[0] + 10, y - 20, "№")
    c.drawString(col_positions[1] + 10, y - 20, "Mahsulot")
    c.drawRightString(col_positions[2] - 10, y - 20, "Miqdor")
    c.drawRightString(col_positions[3] - 10, y - 20, "Narx")
    c.drawRightString(col_positions[4] - 10, y - 20, "Summa")

    # HEADER VERTICAL LINES
    for x in col_positions[1:-1]:
        c.line(x, y - row_height, x, y)

    y -= row_height

    total_sum = 0
    c.setFont("Helvetica", 11)

    for i, item in enumerate(context.user_data["items"], start=1):
        c.rect(table_left, y - row_height, table_right - table_left, row_height, stroke=1, fill=0)

        for x in col_positions[1:-1]:
            c.line(x, y - row_height, x, y)

        c.drawString(col_positions[0] + 10, y - 20, str(i))
        c.drawString(col_positions[1] + 10, y - 20, item["product"])
        c.drawRightString(col_positions[2] - 10, y - 20, str(item["qty"]))
        c.drawRightString(col_positions[3] - 10, y - 20, f"{item['price']:,}")
        c.drawRightString(col_positions[4] - 10, y - 20, f"{item['total']:,}")

        total_sum += item["total"]
        y -= row_height

    # TOTAL
    y -= 40
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(table_right, y, f"JAMI: {total_sum:,} so'm")

    c.line(table_right - 230, y - 5, table_right, y - 5)

    # STAMP
    if os.path.exists("stamp.png"):
        c.drawImage("stamp.png", 60, 90, width=180, height=180, mask='auto')

    # SIGNATURE
    if os.path.exists("signature.png"):
        c.drawImage("signature.png", width - 250, 120, width=180, height=70, mask='auto')

    c.save()

    with open(file_name, "rb") as f:
        await update.message.reply_document(f)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

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
