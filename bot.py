import os
import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.environ.get("BOT_TOKEN")

# তোমার Telegram User ID
ADMIN_ID = 8487698957

DB_NAME = "messages.db"


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_users (
            admin_message_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_message(admin_message_id, user_id):
    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR REPLACE INTO message_users
        (admin_message_id, user_id)
        VALUES (?, ?)
        """,
        (admin_message_id, user_id)
    )

    conn.commit()
    conn.close()


def get_user_id(admin_message_id):
    conn = sqlite3.connect(DB_NAME)

    result = conn.execute(
        """
        SELECT user_id
        FROM message_users
        WHERE admin_message_id = ?
        """,
        (admin_message_id,)
    ).fetchone()

    conn.close()

    return result[0] if result else None


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "হ্যালো! 👋 Hunter Bot চালু হয়েছে!\n\n"
        "তুমি text, photo, video, voice বা file পাঠাতে পারো।"
    )


# =========================
# HELP
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "/start - Bot চালু\n"
        "/help - Help"
    )


# =========================
# USER MESSAGE
# =========================

async def handle_user_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    message = update.message

    username = (
        f"@{user.username}"
        if user.username
        else "নেই"
    )

    info = (
        "━━━━━━━━━━━━━━━━━━\n"
        "📩 নতুন Message\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"🔹 Username: {username}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    sent_message = None

    # TEXT
    if message.text:

        sent_message = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"{info}\n\n"
                f"💬 Message:\n{message.text}"
            )
        )

    # PHOTO
    elif message.photo:

        sent_message = await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=info + "\n\n🖼️ Photo"
        )

    # VIDEO
    elif message.video:

        sent_message = await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=message.video.file_id,
            caption=info + "\n\n🎬 Video"
        )

    # VOICE
    elif message.voice:

        sent_message = await context.bot.send_voice(
            chat_id=ADMIN_ID,
            voice=message.voice.file_id,
            caption=info + "\n\n🎤 Voice"
        )

    # DOCUMENT
    elif message.document:

        sent_message = await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=message.document.file_id,
            caption=info + "\n\n📎 File"
        )

    # STICKER
    elif message.sticker:

        sent_message = await context.bot.send_sticker(
            chat_id=ADMIN_ID,
            sticker=message.sticker.file_id
        )

        # Sticker-এর জন্য আলাদা info message
        info_message = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=info + "\n\n🎨 Sticker"
        )

        save_message(
            info_message.message_id,
            user.id
        )

    # Admin message-এর সাথে user ID save
    if sent_message:

        save_message(
            sent_message.message_id,
            user.id
        )

    # User confirmation
    await message.reply_text(
        "✅ Message পেয়েছি!"
    )


# =========================
# ADMIN REPLY
# =========================

async def admin_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.message

    # শুধু Admin reply করতে পারবে
    if update.effective_user.id != ADMIN_ID:
        return

    # Reply না হলে ignore
    if not message.reply_to_message:
        return

    replied_message_id = (
        message.reply_to_message.message_id
    )

    # Database থেকে user ID বের করি
    user_id = get_user_id(
        replied_message_id
    )

    if not user_id:

        await message.reply_text(
            "❌ এই message-এর user পাওয়া যায়নি।"
        )

        return

    try:

        # TEXT
        if message.text:

            await context.bot.send_message(
                chat_id=user_id,
                text=f"👨‍💻 Admin:\n{message.text}"
            )

        # PHOTO
        elif message.photo:

            await context.bot.send_photo(
                chat_id=user_id,
                photo=message.photo[-1].file_id,
                caption="👨‍💻 Admin"
            )

        # VIDEO
        elif message.video:

            await context.bot.send_video(
                chat_id=user_id,
                video=message.video.file_id,
                caption="👨‍💻 Admin"
            )

        # VOICE
        elif message.voice:

            await context.bot.send_voice(
                chat_id=user_id,
                voice=message.voice.file_id
            )

        # DOCUMENT
        elif message.document:

            await context.bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption="👨‍💻 Admin"
            )

        # STICKER
        elif message.sticker:

            await context.bot.send_sticker(
                chat_id=user_id,
                sticker=message.sticker.file_id
            )

        await message.reply_text(
            "✅ Reply user-এর কাছে পাঠানো হয়েছে!"
        )

    except Exception as e:

        await message.reply_text(
            f"❌ Message পাঠানো যায়নি:\n{e}"
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:

        raise ValueError(
            "BOT_TOKEN environment variable পাওয়া যায়নি!"
        )

    init_db()

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    # Admin reply
    app.add_handler(
        MessageHandler(
            filters.REPLY & ~filters.COMMAND,
            admin_reply
        )
    )

    # User messages
    app.add_handler(
        MessageHandler(
            (
                filters.TEXT
                | filters.PHOTO
                | filters.VIDEO
                | filters.VOICE
                | filters.Document.ALL
                | filters.Sticker.ALL
            )
            & ~filters.COMMAND,
            handle_user_message
        )
    )

    print("🤖 Hunter Bot চলছে...")

    app.run_polling()


if __name__ == "__main__":
    main()
