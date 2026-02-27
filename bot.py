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
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

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
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    blue = colors.HexColor("#1f4e8c")

    # Logo
    if os.path.exists("logo.png"):
        elements.append(Image("logo.png", width=2*inch, height=1*inch))
        elements.append(Spacer(1, 10))

    # Title
    title = Paragraph("<b>UZMARKET OPTOM CHEK</b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Chek info
    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    info_data = [
        ["Sotuvchi:", "UzMarketOptom"],
        ["Manzil:", "Samarqand sh."],
        ["Tel:", "+998 XX XXX XX XX"],
        ["Chek №:", str(chek_no)],
        ["Sana:", today],
    ]

    info_table = Table(info_data, colWidths=[120, 350])
    info_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0,0), (-1,-1), blue),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Items table
    data = [["№", "Mahsulot", "Miqdor", "Narx", "Summa"]]
    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        data.append([
            str(i),
            item["product"],
            str(item["qty"]),
            f"{item['price']:,}",
            f"{item['total']:,}"
        ])
        total_sum += item["total"]

    items_table = Table(data, colWidths=[40, 200, 60, 80, 90])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), blue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, blue),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (2,1), (-1,-1), "CENTER"),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Jami
    jami_paragraph = Paragraph(
        f"<b>JAMI: {total_sum:,} so'm</b>",
        styles["Heading2"]
    )
    elements.append(jami_paragraph)
    elements.append(Spacer(1, 40))

    # Stamp + signature
    if os.path.exists("stamp.png"):
        elements.append(Image("stamp.png", width=2*inch, height=2*inch))

    elements.append(Spacer(1, 20))

    if os.path.exists("signature.png"):
        elements.append(Image("signature.png", width=2*inch, height=1*inch))

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
            ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
