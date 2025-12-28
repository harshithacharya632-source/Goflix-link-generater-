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

    # ✅ VERY IMPORTANT: handle HEAD request
    if request.method == "HEAD":
        return web.Response(
            status=200,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Type": "video/mp4",
            }
        )

    range_header = request.headers.get("Range")

    index = min(work_loads, key=work_loads.get)
    tg_client = multi_clients[index]

    if tg_client in class_cache:
        streamer = class_cache[tg_client]
    else:
        streamer = ByteStreamer(tg_client)
        class_cache[tg_client] = streamer

    file_id = await streamer.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        from_b, to_b = range_header.replace("bytes=", "").split("-")
        from_b = int(from_b)
        to_b = int(to_b) if to_b else file_size - 1
    else:
        from_b = 0
        to_b = file_size - 1

    chunk_size = 1024 * 1024
    body = streamer.yield_file(
        file_id, index,
        from_b, 0, (to_b - from_b + 1),
        1, chunk_size
    )

    # ✅ FORCE MIME FOR STREAM
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
            "Content-Length": str(to_b - from_b + 1),
            "Content-Range": f"bytes {from_b}-{to_b}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'{disposition}; filename="{file_id.file_name}"',
            "Cache-Control": "no-cache",
        }
    )
