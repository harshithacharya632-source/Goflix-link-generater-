# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, math, logging, secrets, mimetypes
from info import *
from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine
from TechVJ.bot import multi_clients, work_loads
from TechVJ.server.exceptions import FIleNotFound, InvalidHash
from TechVJ.util.custom_dl import ByteStreamer
from TechVJ.util.render_template import render_page

routes = web.RouteTableDef()

# ---------- ROOT (Health check) ----------
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.Response(text="OK", status=200)


# ---------- WATCH PAGE ----------
@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_page(request: web.Request):
    try:
        path = request.match_info["path"]
        id = int(re.search(r"(\d+)", path).group(1))
        secure_hash = request.rel_url.query.get("hash")
        return web.Response(
            text=await render_page(id, secure_hash),
            content_type="text/html"
        )
    except Exception:
        raise web.HTTPNotFound()


# ---------- STREAM / DOWNLOAD ----------
@routes.get(r"/{path:\S+}", allow_head=True)
async def file_handler(request: web.Request):
    try:
        path = request.match_info["path"]
        id = int(re.search(r"(\d+)", path).group(1))
        secure_hash = request.rel_url.query.get("hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash:
        raise web.HTTPForbidden()
    except FIleNotFound:
        raise web.HTTPNotFound()


# ---------- STREAM CORE ----------
class_cache = {}

async def media_streamer(request: web.Request, id: int, secure_hash: str):

    range_header = request.headers.get("Range")

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    tg_connect = class_cache.get(faster_client)
    if not tg_connect:
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    # ---- RANGE PARSING ----
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        from_bytes = int(match.group(1))
        until_bytes = int(match.group(2)) if match.group(2) else file_size - 1
        status = 206
    else:
        from_bytes = 0
        until_bytes = file_size - 1
        status = 200

    if until_bytes >= file_size or from_bytes < 0:
        return web.Response(
            status=416,
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    # ---- STREAM SETUP ----
    chunk_size = 1024 * 1024
    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    req_length = until_bytes - from_bytes + 1

    mime_type = file_id.mime_type or "application/octet-stream"
    file_name = file_id.file_name or "file.bin"

    response = web.StreamResponse(
        status=status,
        headers={
            "Content-Type": mime_type,
            "Content-Length": str(req_length),
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }
    )

    await response.prepare(request)

    try:
        async for chunk in tg_connect.yield_file(
            file_id,
            index,
            offset,
            first_part_cut,
            last_part_cut,
            part_count,
            chunk_size
        ):
            await response.write(chunk)
    finally:
        await response.write_eof()

    return response



