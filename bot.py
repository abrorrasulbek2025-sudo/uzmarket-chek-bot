ADMIN_ID = 6056893338
import os
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

TOKEN = os.getenv("BOT_TOKEN")

PRODUCT, QTY, PRICE, ADD_MORE = range(4)

def get_next_chek_number():
    if not os.path.exists("chek_id.txt"):
        with open("chek_id.txt", "w") as f:
            f.write("1")
        return "0001"

    with open("chek_id.txt", "r") as f:
        number = int(f.read())

    with open("chek_id.txt", "w") as f:
        f.write(str(number + 1))

    return str(number).zfill(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return ConversationHandler.END

    context.user_data["items"] = []
    await update.message.reply_text("Mahsulot nomini kiriting:")
    return PRODUCT

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_product"] = update.message.text
    await update.message.reply_text("Miqdorni kiriting:")
    return QTY

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_qty"] = int(update.message.text)
    await update.message.reply_text("Narxni kiriting:")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product = context.user_data["current_product"]
    qty = context.user_data["current_qty"]
    price = int(update.message.text)

    total = qty * price

    context.user_data["items"].append({
        "product": product,
        "qty": qty,
        "price": price,
        "total": total
    })

    keyboard = [["Ha", "Yo'q"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text("Yana mahsulot qo‘shasizmi?", reply_markup=reply_markup)
    return ADD_MORE

async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Ha":
        await update.message.reply_text("Mahsulot nomini kiriting:")
        return PRODUCT
    else:
        await generate_pdf(update, context)
        return ConversationHandler.END

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = "chek.pdf"
    doc = SimpleDocTemplate(filename)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        alignment=1,
        textColor=colors.HexColor("#1F4E8C"),
        fontSize=20
    )

    elements.append(Image("logo.png", width=2*inch, height=1*inch))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>UZMARKETOPTOM SAVDO CHEKI</b>", title_style))
    elements.append(Spacer(1, 20))

    now = datetime.datetime.now().strftime("%d.%m.%Y")
    chek_no = get_next_chek_number()

    elements.append(Paragraph("Sotuvchi: UzMarketOptom", styles["Normal"]))
    elements.append(Paragraph("Manzil: Samarqand sh.", styles["Normal"]))
    elements.append(Paragraph("Tel: +998 97 446 72 82 / +998 94 754 49 30", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Chek № {chek_no}", styles["Normal"]))
    elements.append(Paragraph(f"Sana: {now}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["№", "Mahsulot", "Miqdor", "Narx", "Jami"]]

    total_sum = 0

    for i, item in enumerate(context.user_data["items"], start=1):
        data.append([
            str(i),
            item["product"],
            str(item["qty"]),
            str(item["price"]),
            str(item["total"])
        ])
        total_sum += item["total"]

    table = Table(data)
    table.setStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("GRID", (0,0), (-1,-1), 1, colors.grey)
    ])

    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>JAMI: {total_sum} so‘m</b>", styles["Heading2"]))
    elements.append(Spacer(1, 40))
    elements.append(Image("stamp.png", width=2*inch, height=2*inch))

    doc.build(elements)

    await update.message.reply_document(open(filename, "rb"))

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("chek", start)],
    states={
        PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product)],
        QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)
app.run_polling()
