import asyncio
import humanize

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

    await message.reply_text(
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

    # Send file to LOG_CHANNEL
    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=file_id
    )

    file_name = get_name(log_msg)

    # # Generate links
    # if not SHORTLINK:
    #     stream = f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    #     download = f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    # else:
    #     stream = await get_shortlink(
    #         f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    #     )
    #     download = await get_shortlink(
    #         f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
    #     )
    # Generate links
    if not SHORTLINK:
        # Player page
        watch = f"{URL}/watch/{log_msg.id}?hash={get_hash(log_msg)}"
    
        # 🔥 DIRECT STREAM (USED BY WEB PLAYER)
        stream = f"{URL}/{log_msg.id}?hash={get_hash(log_msg)}"
    
        # Download
        download = f"{URL}/download/{log_msg.id}?hash={get_hash(log_msg)}"
    
    else:
        watch = await get_shortlink(
            f"{URL}/watch/{log_msg.id}?hash={get_hash(log_msg)}"
        )
    
        stream = await get_shortlink(
            f"{URL}/{log_msg.id}?hash={get_hash(log_msg)}"
        )
    
        download = await get_shortlink(
            f"{URL}/download/{log_msg.id}?hash={get_hash(log_msg)}"
        )


    # Buttons
    rm = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🖥 Stream", url=stream),
            InlineKeyboardButton("📥 Download", url=download)
        ]]
    )

    # Bot link message
    bot_msg = await message.reply_text(
        text=(
            "<b>✅ Your link is ready!</b>\n\n"
            f"<b>📂 File:</b> <i>{file_name}</i>\n"
            f"<b>📦 Size:</b> <i>{humanbytes(get_media_file_size(message))}</i>\n\n"
            "<b>⏳ Auto Delete:</b>\n"
            "• User file → 30 seconds\n"
            "• Link message → 3 minutes"
        ),
        reply_markup=rm,
        disable_web_page_preview=True
    )

    # =========================
    # DELETE USER FILE (30s)
    # =========================
    async def delete_user_file():
        await asyncio.sleep(30)
        try:
            await message.delete()
        except Exception as e:
            print(f"User file delete failed: {e}")

    # =========================
    # DELETE BOT LINK (180s)
    # =========================
    async def delete_bot_message():
        await asyncio.sleep(180)
        try:
            await bot_msg.delete()
        except Exception as e:
            print(f"Bot message delete failed: {e}")

    asyncio.create_task(delete_user_file())
    asyncio.create_task(delete_bot_message())

