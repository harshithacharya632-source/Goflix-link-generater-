import random
import humanize
import asyncio

from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import URL, LOG_CHANNEL, SHORTLINK
from urllib.parse import quote_plus

from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink


# =========================
# START COMMAND
# =========================
@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 Welcome to Stream Bot!\n\n"
        "🎬 Stream movies & series instantly\n"
        "⚡ Fast & smooth streaming\n"
        "📥 No waiting, no limits\n"
        "🛠 Admin support available\n\n"
        "Click below to stay updated 👇",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✨ Update Channel", url="https://t.me/trendi_Backup")]]
        )
    )
    await client.send_message(
        chat_id=message.from_user.id,
        text=script.START_TXT.format(
            message.from_user.mention,
            temp.U_NAME,
            temp.B_NAME
        ),
        reply_markup=rm,
        parse_mode=enums.ParseMode.HTML
    )


# =========================
# FILE → LINK HANDLER
# =========================
@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):

    file = getattr(message, message.media.value)
    file_id = file.file_id
    user_id = message.from_user.id
    username = message.from_user.mention

    # Forward file to LOG_CHANNEL
    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=file_id
    )

    file_name = get_name(log_msg)
    file_hash = get_hash(log_msg)

    # =========================
    # LINK GENERATION
    # =========================
    if not SHORTLINK:
        stream = f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
        download = f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
    else:
        stream = await get_shortlink(
            f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
        )
        download = await get_shortlink(
            f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
        )

    # =========================
    # LOG MESSAGE
    # =========================
    await log_msg.reply_text(
        text=(
            f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id}\n"
            f"•• ᴜꜱᴇʀɴᴀᴍᴇ : {username}\n\n"
            f"•• ғɪʟᴇ ɴᴀᴍᴇ : {file_name}"
        ),
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🖥 Watch Online", url=stream),
                InlineKeyboardButton("📥 Download", url=download)
            ]]
        ),
        disable_web_page_preview=True
    )

    # =========================
    # USER BUTTONS
    # =========================
    rm = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🖥 Stream", url=stream),
            InlineKeyboardButton("📥 Download", url=download)
        ]]
    )

    msg_text = (
        "<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱!</u></i>\n\n"
        f"<b>📂 File Name:</b> <i>{file_name}</i>\n\n"
        f"<b>📦 File Size:</b> <i>{humanbytes(get_media_file_size(message))}</i>\n\n"
        "<b>⏳ This message will be auto-deleted in 5 minutes</b>"
    )

    main_msg = await message.reply_text(
        text=msg_text,
        reply_markup=rm,
        disable_web_page_preview=True
    )

    # =========================
    # AUTO DELETE USER FILE (20s)
    # =========================
    async def delete_user_file():
        await asyncio.sleep(20)
        try:
            await message.delete()
        except Exception as e:
            print(f"User file delete failed: {e}")

    # =========================
    # AUTO DELETE BOT MESSAGE (5 min)
    # =========================
    async def delete_bot_message():
        await asyncio.sleep(300)  # 5 minutes
        try:
            await main_msg.delete()
        except Exception as e:
            print(f"Bot message delete failed: {e}")

    asyncio.create_task(delete_user_file())
    asyncio.create_task(delete_bot_message())
