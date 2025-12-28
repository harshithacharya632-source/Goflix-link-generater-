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

    is_watch = request.path.startswith("/watch")

    # ✅ Handle HEAD (Koyeb requirement)
    if request.method == "HEAD":
        return web.Response(
            status=200,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Type": "video/mp4",
            }
        )

    range_header = request.headers.get("Range", 0)

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
    else:
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    # ---- RANGE CALCULATION (RESTORED – IMPORTANT) ----
    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)

    body = tg_connect.yield_file(
        file_id,
        index,
        offset,
        first_part_cut,
        last_part_cut,
        part_count,
        chunk_size
    )

    # ---- MIME + DISPOSITION ----
    if is_watch:
        mime_type = "video/mp4"
        disposition = "inline"
    else:
        mime_type = file_id.mime_type or "application/octet-stream"
        disposition = "attachment"

    return web.Response(
        status=206,
        body=body,
        headers={
            "Content-Type": mime_type,
            "Content-Length": str(req_length),
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'{disposition}; filename="{file_id.file_name}"',
            "Cache-Control": "no-cache",
        },
    )

