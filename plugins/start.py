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
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL,
            script.LOG_TEXT_P.format(
                message.from_user.id,
                message.from_user.mention
            )
        )

    rm = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✨ Update Channel", url="https://t.me/trendi_Backup")]]
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
# FILE TO LINK HANDLER
# =========================
@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    file = getattr(message, message.media.value)

    fileid = file.file_id
    user_id = message.from_user.id
    username = message.from_user.mention

    # Forward file to LOG_CHANNEL
    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=fileid
    )

    file_name = get_name(log_msg)

    # Generate links
    if SHORTLINK is False:
        stream = f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
        download = f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    else:
        stream = await get_shortlink(
            f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
        )
        download = await get_shortlink(
            f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
        )

    # Log info in LOG_CHANNEL
    await log_msg.reply_text(
        text=(
            f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id}\n"
            f"•• ᴜꜱᴇʀɴᴀᴍᴇ : {username}\n\n"
            f"•• ᖴɪʟᴇ Nᴀᴍᴇ : {file_name}"
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                InlineKeyboardButton("🖥 Watch Online 🖥", url=stream)
            ]]
        )
    )

    # Buttons for user
    rm = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🖥 Stream", url=stream),
            InlineKeyboardButton("📥 Download", url=download)
        ]]
    )

    msg_text = (
        "<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱!</u></i>\n\n"
        "<b>📂 File Name:</b> <i>{}</i>\n\n"
        "<b>📦 File Size:</b> <i>{}</i>\n\n"
        "<b>🚸 NOTE:</b> User uploaded file will be "
        "deleted automatically in <b>120 seconds</b>."
    )

    await message.reply_text(
        text=msg_text.format(
            file_name,
            humanbytes(get_media_file_size(message))
        ),
        disable_web_page_preview=True,
        reply_markup=rm
    )

    # =========================
    # AUTO DELETE USER FILE (120s)
    # =========================
    async def delete_user_file():
        await asyncio.sleep(120)
        try:
            await message.delete()
            print(f"User file deleted: {user_id}")
        except Exception as e:
            print(f"Failed to delete user file: {e}")

    asyncio.create_task(delete_user_file())
