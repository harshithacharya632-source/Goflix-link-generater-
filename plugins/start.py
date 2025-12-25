# import asyncio
# import humanize
# from urllib.parse import quote_plus

# from pyrogram import Client, filters, enums
# from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# from Script import script
# from info import URL, LOG_CHANNEL, SHORTLINK
# from database.users_chats_db import db
# from utils import temp, get_shortlink

# from TechVJ.util.file_properties import (
#     get_name,
#     get_hash,
#     get_media_file_size
# )
# from TechVJ.util.human_readable import humanbytes


# # =========================
# # START COMMAND
# # =========================
# @Client.on_message(filters.private & filters.command("start", prefixes=["/"]))
# async def start(client, message):
#     print("✅ /start triggered")

#     user = message.from_user
#     if not user:
#         return

#     # Save user
#     try:
#         if not await db.is_user_exist(user.id):
#             await db.add_user(user.id, user.first_name or "User")

#             await client.send_message(
#                 LOG_CHANNEL,
#                 f"👤 <b>New User Started Bot</b>\n\n"
#                 f"🆔 ID: <code>{user.id}</code>\n"
#                 f"👤 User: {user.mention}",
#                 parse_mode=enums.ParseMode.HTML
#             )
#     except Exception as e:
#         print(f"DB / LOG error: {e}")

#     # Buttons
#     buttons = InlineKeyboardMarkup(
#         [[
#             InlineKeyboardButton("✨ Update Channel", url="https://t.me/trendi_Backup")
#         ]]
#     )

#     # Start message (SAFE)
#     start_text = (
#         f"<b>Hello {user.first_name} 👋</b>\n\n"
#         f"Welcome to <b>{temp.B_NAME}</b> 🤖\n"
#         f"Maintained by <b>{temp.U_NAME}</b>\n"
#         f"👑 Admin Bot : <b>@Goflix_AdminBot</b>\n\n"
#         f"📤 Send me a file to generate stream & download links."
#     )

#     await message.reply_text(
#         text=start_text,
#         reply_markup=buttons,
#         parse_mode=enums.ParseMode.HTML,
#         disable_web_page_preview=True
#     )


# # =========================
# # FILE HANDLER
# # =========================
# @Client.on_message(filters.private & (filters.document | filters.video))
# async def stream_start(client, message):
#     user = message.from_user
#     if not user:
#         return

#     file = getattr(message, message.media.value)
#     fileid = file.file_id
#     user_id = user.id
#     username = user.mention

#         # 🔴 DELETE USER SENT FILE AFTER 20 SECONDS
#     async def delete_user_file():
#         await asyncio.sleep(20)
#         try:
#             await message.delete()
#             print(f"User file deleted: {user_id}")
#         except Exception as e:
#             print(f"User file delete error: {e}")

#     asyncio.create_task(delete_user_file())

#     # Send file to LOG_CHANNEL
#     log_msg = await client.send_cached_media(
#         chat_id=LOG_CHANNEL,
#         file_id=fileid
#     )

#     file_name = get_name(log_msg)

#     # Generate links
#     if not SHORTLINK:
#         stream = f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
#         download = f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
#     else:
#         stream = await get_shortlink(
#             f"{URL}/watch/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
#         )
#         download = await get_shortlink(
#             f"{URL}/download/{log_msg.id}/{quote_plus(file_name)}?hash={get_hash(log_msg)}"
#         )

#     # Log message
#     await log_msg.reply_text(
#         text=(
#             f"🔗 <b>Link Generated</b>\n\n"
#             f"🆔 User ID: <code>{user_id}</code>\n"
#             f"👤 User: {username}\n\n"
#             f"📂 File: <code>{file_name}</code>"
#         ),
#         parse_mode=enums.ParseMode.HTML,
#         disable_web_page_preview=True,
#         reply_markup=InlineKeyboardMarkup(
#             [[
#                 InlineKeyboardButton("🚀 Fast Download", url=download),
#                 InlineKeyboardButton("🖥 Watch Online", url=stream)
#             ]]
#         )
#     )

#     # Buttons for user
#     user_buttons = InlineKeyboardMarkup(
#         [[
#             InlineKeyboardButton("🖥 Stream", url=stream),
#             InlineKeyboardButton("📥 Download", url=download)
#         ]]
#     )

#     # Message text
#     msg_text = (
#         "<i><u>Your Link Generated!</u></i>\n\n"
#         f"<b>📂 File Name:</b> <i>{file_name}</i>\n\n"
#         f"<b>📦 File Size:</b> <i>{humanbytes(get_media_file_size(message))}</i>\n\n"
#         "<b>⏳ This message will be deleted in 120 seconds</b>"
#     )

#     main_msg = await message.reply_text(
#         text=msg_text,
#         parse_mode=enums.ParseMode.HTML,
#         reply_markup=user_buttons,
#         disable_web_page_preview=True
#     )

#     # Auto delete
#     async def auto_delete():
#         await asyncio.sleep(120)
#         try:
#             await main_msg.delete()
#         except Exception as e:
#             print(f"Auto-delete error: {e}")

#     asyncio.create_task(auto_delete())



import asyncio
from urllib.parse import quote_plus

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import URL, LOG_CHANNEL
from database.users_chats_db import db
from utils import temp

from TechVJ.util.file_properties import (
    get_name,
    get_hash,
    get_media_file_size
)
from TechVJ.util.human_readable import humanbytes


# =========================
# START COMMAND
# =========================
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):

    user = message.from_user
    if not user:
        return

    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name or "User")

    await message.reply_text(
        text=(
            f"<b>Hello {user.first_name} 👋</b>\n\n"
            f"Welcome to <b>{temp.B_NAME}</b> 🤖\n\n"
            f"📤 Send me a file to generate Stream & Download links."
        ),
        parse_mode=enums.ParseMode.HTML
    )


# =========================
# FILE HANDLER
# =========================
@Client.on_message(filters.private & (filters.document | filters.video))
async def file_handler(client, message):

    user = message.from_user
    if not user:
        return

    media = getattr(message, message.media.value)
    file_id = media.file_id

    # Send file to LOG_CHANNEL
    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=file_id
    )

    file_name = get_name(log_msg)
    msg_id = log_msg.id
    file_hash = get_hash(log_msg)

    # Generate links
    stream = f"{URL}/watch/{msg_id}/{quote_plus(file_name)}?hash={file_hash}"
    download = f"{URL}/download/{msg_id}/{quote_plus(file_name)}?hash={file_hash}"

    buttons = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🖥 Stream", url=stream),
            InlineKeyboardButton("📥 Download", url=download)
        ]]
    )

    await message.reply_text(
        text=(
            "<b>✅ Link Generated</b>\n\n"
            f"📂 <b>File:</b> <i>{file_name}</i>\n"
            f"📦 <b>Size:</b> <i>{humanbytes(get_media_file_size(message))}</i>\n\n"
            "⚠️ Links are private & temporary"
        ),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

