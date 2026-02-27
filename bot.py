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
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ======================
# CONFIG
# ======================

ADMIN_ID = 6056893338
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi.")

PRODUCT, QTY, PRICE, ADD_MORE = range(4)

BRAND_BLUE = colors.HexColor("#1f4e8c")

# ======================
# TELEGRAM HANDLERS
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
# PROFESSIONAL PDF
# ======================

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file_name = "chek.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []

    # ===== LOGO =====
    if os.path.exists("logo.png"):
        elements.append(Image("logo.png", width=3*inch, height=1.2*inch))
        elements.append(Spacer(1, 0.2*inch))

    # ===== HEADER INFO =====
    chek_no = random.randint(1000, 9999)
    today = datetime.datetime.now().strftime("%d.%m.%Y")

    header_data = [
        ["Sotuvchi: UzMarketOptom", f"Chek № {chek_no}"],
        ["Manzil: Samarqand sh.", f"Sana: {today}"],
        ["Tel: +998 XX XXX XX XX", ""],
    ]

    header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0,0), (-1,-1), BRAND_BLUE),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # ===== ITEMS TABLE =====
    data = [["№", "Mahsulot", "Miqdor", "Narx", "Summa"]]

    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        data.append([
            i,
            item["product"],
            item["qty"],
            f"{item['price']:,}",
            f"{item['total']:,}"
        ])
        total_sum += item["total"]

    table = Table(data, colWidths=[0.7*inch, 2.8*inch, 1*inch, 1.2*inch, 1.2*inch])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, BRAND_BLUE),
        ("BACKGROUND", (0,0), (-1,0), BRAND_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.4*inch))

    # ===== TOTAL =====
    total_table = Table(
        [["JAMI:", f"{total_sum:,} so'm"]],
        colWidths=[4.7*inch, 1.2*inch]
    )

    total_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0,0), (-1,-1), BRAND_BLUE),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 14),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
    ]))

    elements.append(total_table)
    elements.append(Spacer(1, 0.8*inch))

    # ===== STAMP & SIGNATURE =====
    footer_data = []

    stamp = Image("stamp.png", width=2*inch, height=2*inch) if os.path.exists("stamp.png") else ""
    sign = Image("signature.png", width=2*inch, height=0.8*inch) if os.path.exists("signature.png") else ""

    footer_data.append([stamp, sign])

    footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
    elements.append(footer_table)

    doc.build(elements)

    with open(file_name, "rb") as f:
        await update.message.reply_document(f)

    return ConversationHandler.END

# ======================
# MAIN
# ======================

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
