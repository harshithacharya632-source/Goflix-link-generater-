import jinja2
import urllib.parse
import logging
import aiohttp

from info import *
from TechVJ.bot import TechVJBot
from TechVJ.util.human_readable import humanbytes
from TechVJ.util.file_properties import get_file_ids
from TechVJ.server.exceptions import InvalidHash


async def render_page(id, secure_hash):
    # Fetch message & file info
    file = await TechVJBot.get_messages(int(LOG_CHANNEL), int(id))
    file_data = await get_file_ids(
        TechVJBot,
        int(LOG_CHANNEL),
        int(id)
    )

    # Validate hash
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(
            f"Invalid hash: {secure_hash} != {file_data.unique_id[:6]}"
        )
        raise InvalidHash

    # Detect media type
    mime_main = file_data.mime_type.split("/")[0].strip()
    file_size = humanbytes(file_data.file_size)
    file_name = file_data.file_name.replace("_", " ")

    # -------- URL SELECTION --------
    if mime_main in ["video", "audio"]:
        # STREAM URL (IMPORTANT)
        file_url = urllib.parse.urljoin(
            URL,
            f"stream/{id}?hash={secure_hash}"
        )
        template_file = "TechVJ/template/req.html"
    else:
        # DOWNLOAD URL
        file_url = urllib.parse.urljoin(
            URL,
            f"download/{id}?hash={secure_hash}"
        )
        template_file = "TechVJ/template/dl.html"

        # Re-check size from headers (optional, keep your logic)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(file_url) as u:
                    if u.headers.get("Content-Length"):
                        file_size = humanbytes(
                            int(u.headers["Content-Length"])
                        )
        except Exception:
            pass

    # Load template
    with open(template_file, "r", encoding="utf-8") as f:
        template = jinja2.Template(f.read())

    # Render HTML
    return template.render(
        file_name=file_name,
        file_url=file_url,      # 🔥 THIS IS NOW /stream or /download
        file_size=file_size,
        file_unique_id=file_data.unique_id,
    )
