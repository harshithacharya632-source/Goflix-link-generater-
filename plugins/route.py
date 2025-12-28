# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, math, logging, secrets
from aiohttp import web
from info import *
from TechVJ.bot import multi_clients, work_loads
from TechVJ.server.exceptions import FIleNotFound, InvalidHash
from TechVJ.util.custom_dl import ByteStreamer
from TechVJ.util.render_template import render_page

routes = web.RouteTableDef()
class_cache = {}

# ---------------- ROOT (Health) ----------------
@routes.get("/", allow_head=True)
async def root(request):
    return web.Response(text="OK", status=200)


# ---------------- WATCH PAGE ----------------
@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_page(request: web.Request):
    try:
        path = request.match_info["path"]
        id = int(re.search(r"(\d+)", path).group(1))
        secure_hash = request.rel_url.query.get("hash")

        # IMPORTANT: render_page must use /stream URL
        return web.Response(
            text=await render_page(id, secure_hash),
            content_type="text/html"
        )
    except Exception:
        raise web.HTTPNotFound()


# ---------------- STREAM (INLINE) ----------------
@routes.get(r"/stream/{path:\S+}", allow_head=True)
async def stream_handler(request: web.Request):
    path = request.match_info["path"]
    id = int(re.search(r"(\d+)", path).group(1))
    secure_hash = request.rel_url.query.get("hash")
    return await media_streamer(request, id, secure_hash, inline=True)


# ---------------- DOWNLOAD ----------------
@routes.get(r"/download/{path:\S+}", allow_head=True)
async def download_handler(request: web.Request):
    path = request.match_info["path"]
    id = int(re.search(r"(\d+)", path).group(1))
    secure_hash = request.rel_url.query.get("hash")
    return await media_streamer(request, id, secure_hash, inline=False)


# ---------------- CORE STREAMER ----------------
async def media_streamer(
    request: web.Request,
    id: int,
    secure_hash: str,
    inline: bool
):
    range_header = request.headers.get("Range")

    index = min(work_loads, key=work_loads.get)
    client = multi_clients[index]

    tg = class_cache.get(client)
    if not tg:
        tg = ByteStreamer(client)
        class_cache[client] = tg

    file_id = await tg.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    # -------- RANGE --------
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        status = 206
    else:
        start = 0
        end = file_size - 1
        status = 200

    if end >= file_size or start < 0:
        return web.Response(
            status=416,
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    chunk_size = 1024 * 1024
    offset = start - (start % chunk_size)
    first_cut = start - offset
    last_cut = end % chunk_size + 1
    part_count = math.ceil(end / chunk_size) - math.floor(offset / chunk_size)
    length = end - start + 1

    mime = file_id.mime_type or "application/octet-stream"
    name = file_id.file_name or "file.bin"

    response = web.StreamResponse(
        status=status,
        headers={
            "Content-Type": mime,
            "Content-Length": str(length),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Disposition": (
                f'inline; filename="{name}"'
                if inline else
                f'attachment; filename="{name}"'
            ),
        }
    )

    await response.prepare(request)

    async for chunk in tg.yield_file(
        file_id,
        index,
        offset,
        first_cut,
        last_cut,
        part_count,
        chunk_size
    ):
        await response.write(chunk)

    await response.write_eof()
    return response
