import os
import subprocess
from flask import Flask, send_file, abort

app = Flask(__name__)

# Folder where your MKV files are stored
MEDIA_DIR = "downloads"


def abs_path(filename):
    path = os.path.abspath(os.path.join(MEDIA_DIR, filename))
    if not path.startswith(os.path.abspath(MEDIA_DIR)):
        abort(403)
    return path


# =========================
# WATCH (STREAM - WORKING)
# =========================
@app.route("/watch/<path:filename>")
def watch(filename):
    mkv_path = abs_path(filename)

    if not os.path.exists(mkv_path):
        abort(404)

    # Convert MKV -> MP4 (FAST, NO RE-ENCODE)
    mp4_path = mkv_path + ".mp4"

    if not os.path.exists(mp4_path):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", mkv_path,
                "-c", "copy",
                "-movflags", "faststart",
                mp4_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # Stream MP4 with RANGE support (CRITICAL)
    return send_file(
        mp4_path,
        mimetype="video/mp4",
        conditional=True   # 🔥 THIS enables smooth Chrome playback
    )


# =========================
# DOWNLOAD (ORIGINAL FILE)
# =========================
@app.route("/download/<path:filename>")
def download(filename):
    file_path = abs_path(filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_file(
        file_path,
        as_attachment=True
    )


# =========================
# ROOT
# =========================
@app.route("/")
def home():
    return "Goflix streaming server running ✅"


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, threaded=True)
