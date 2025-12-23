import os
import subprocess
from flask import Flask, Response, send_file, abort, request

app = Flask(__name__)

# 🔧 CHANGE THIS PATH to where your files are stored
MEDIA_ROOT = "downloads"


def safe_path(path):
    full_path = os.path.abspath(os.path.join(MEDIA_ROOT, path))
    if not full_path.startswith(os.path.abspath(MEDIA_ROOT)):
        abort(403)
    return full_path


# =========================
# WATCH (STREAM)
# =========================
@app.route("/watch/<path:filename>")
def watch(filename):
    file_path = safe_path(filename)

    if not os.path.exists(file_path):
        abort(404)

    # 🔥 FFmpeg transmux: MKV → MP4 (no re-encode)
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", file_path,
        "-c", "copy",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov",
        "pipe:1"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    def generate():
        try:
            while True:
                chunk = process.stdout.read(1024 * 64)
                if not chunk:
                    break
                yield chunk
        finally:
            process.kill()

    return Response(
        generate(),
        mimetype="video/mp4",
        headers={
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache"
        }
    )


# =========================
# DOWNLOAD
# =========================
@app.route("/download/<path:filename>")
def download(filename):
    file_path = safe_path(filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )


# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def index():
    return "Goflix streaming server running ✅"


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
