# import os
# import subprocess
# from flask import Flask, send_file, abort

# app = Flask(__name__)

# # Folder where your MKV files are stored
# MEDIA_DIR = "downloads"


# def abs_path(filename):
#     path = os.path.abspath(os.path.join(MEDIA_DIR, filename))
#     if not path.startswith(os.path.abspath(MEDIA_DIR)):
#         abort(403)
#     return path


# # =========================
# # WATCH (STREAM - WORKING)
# # =========================
# @app.route("/watch/<path:filename>")
# def watch(filename):
#     mkv_path = abs_path(filename)

#     if not os.path.exists(mkv_path):
#         abort(404)

#     # Convert MKV -> MP4 (FAST, NO RE-ENCODE)
#     mp4_path = mkv_path + ".mp4"

#     if not os.path.exists(mp4_path):
#         subprocess.run(
#             [
#                 "ffmpeg",
#                 "-y",
#                 "-i", mkv_path,
#                 "-c", "copy",
#                 "-movflags", "faststart",
#                 mp4_path
#             ],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL
#         )

#     # Stream MP4 with RANGE support (CRITICAL)
#     return send_file(
#         mp4_path,
#         mimetype="video/mp4",
#         conditional=True   # 🔥 THIS enables smooth Chrome playback
#     )


# # =========================
# # DOWNLOAD (ORIGINAL FILE)
# # =========================
# @app.route("/download/<path:filename>")
# def download(filename):
#     file_path = abs_path(filename)

#     if not os.path.exists(file_path):
#         abort(404)

#     return send_file(
#         file_path,
#         as_attachment=True
#     )


# # =========================
# # ROOT
# # =========================
# @app.route("/")
# def home():
#     return "Goflix streaming server running ✅"


# # =========================
# # MAIN
# # =========================
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 8000))
#     app.run(host="0.0.0.0", port=port, threaded=True)


import os
from flask import Flask, request, Response, abort
from pyrogram import Client

app = Flask(__name__)

# =========================
# ENV VARIABLES (Koyeb)
# =========================
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
LOG_CHANNEL = int(os.environ["LOG_CHANNEL"])

# =========================
# TELEGRAM CLIENT
# =========================
tg = Client(
    "web_stream",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4,
    in_memory=True
)


# =========================
# STREAM (WATCH)
# =========================
@app.route("/watch/<int:msg_id>/<path:filename>")
def watch(msg_id, filename):

    range_header = request.headers.get("Range", None)

    with tg:
        msg = tg.get_messages(LOG_CHANNEL, msg_id)
        if not msg:
            abort(404)

        file = msg.video or msg.document
        if not file:
            abort(404)

        file_size = file.file_size
        start = 0
        end = file_size - 1

        if range_header:
            bytes_range = range_header.replace("bytes=", "").split("-")
            start = int(bytes_range[0])
            if bytes_range[1]:
                end = int(bytes_range[1])

        chunk_size = 1024 * 1024  # 1MB

        def generate():
            offset = start
            while offset <= end:
                limit = min(chunk_size, end - offset + 1)
                for chunk in tg.stream_media(file, offset=offset, limit=limit):
                    yield chunk
                offset += limit

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "video/mp4"
        }

        return Response(generate(), status=206, headers=headers)


# =========================
# DOWNLOAD
# =========================
@app.route("/download/<int:msg_id>/<path:filename>")
def download(msg_id, filename):

    with tg:
        msg = tg.get_messages(LOG_CHANNEL, msg_id)
        if not msg:
            abort(404)

        file = msg.video or msg.document

        def generate():
            for chunk in tg.stream_media(file):
                yield chunk

        return Response(
            generate(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/octet-stream"
            }
        )


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "✅ Goflix Streaming Server Running"


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
