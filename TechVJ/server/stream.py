from aiohttp import web
import re

from info import *
from TechVJ.bot import TechVJBot
from TechVJ.util.file_properties import get_file_ids
from TechVJ.server.exceptions import InvalidHash

CHUNK_SIZE = 512 * 1024  # 512 KB


async def stream_handler(request: web.Request):
    file_id = int(request.match_info["id"])
    secure_hash = request.query.get("hash")

    # Validate file
    file_data = await get_file_ids(
        TechVJBot,
        int(LOG_CHANNEL),
        file_id
    )

    if file_data.unique_id[:6] != secure_hash:
        raise web.HTTPForbidden(text="Invalid hash")

    file_size = file_data.file_size
    mime_type = file_data.mime_type or "video/x-matroska"

    range_header = request.headers.get("Range")

    start = 0
    end = file_size - 1

    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            if match.group(2):
                end = int(match.group(2))

    length = end - start + 1

    headers = {
        "Content-Type": mime_type,
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Range": f"bytes {start}-{end}/{file_size}",
    }

    response = web.StreamResponse(
        status=206 if range_header else 200,
        headers=headers
    )

    await response.prepare(request)

    # Stream from Telegram
    async for chunk in TechVJBot.stream_media(
        LOG_CHANNEL,
        file_id,
        offset=start,
        limit=length
    ):
        await response.write(chunk)

    await response.write_eof()
    return response
