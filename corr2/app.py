"""app.py - Homework Checker"""
import os
from pathlib import Path
from flask import Flask, redirect, render_template, request, url_for, flash, jsonify
from werkzeug.utils import secure_filename

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED    = {"png","jpg","jpeg","bmp"}

app = Flask(__name__)
app.secret_key = "hw-checker-2024"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

def _ok(fn): return "." in fn and fn.rsplit(".",1)[1].lower() in ALLOWED

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    from checker import grade
    from ocr import extract_answers_debug
    import re

    file = request.files.get("file")
    answers_raw = request.form.get("answers_raw", "") # รับเฉลยจากหน้าเว็บ
    
    if not file or not file.filename:
        flash("กรุณาเลือกไฟล์","error"); return redirect(url_for("index"))
    if not _ok(file.filename):
        flash("รองรับ PNG/JPG/JPEG/BMP","error"); return redirect(url_for("index"))
    
    # จัดการเฉลยที่กรอกมา: แยกด้วยบรรทัดหรือคอมมา
    user_key = [a.strip() for a in re.split(r'[\n,]+', answers_raw.strip()) if a.strip()]

    path = UPLOAD_DIR / secure_filename(file.filename)
    file.save(path)
    
    try:
        # ส่ง user_key ไปตรวจ
        result = grade(str(path), provided_key=user_key)
        _, steps = extract_answers_debug(str(path))
        return render_template("result.html", result=result, steps=steps)
    except Exception as e:
        flash(f"Error: {e}","error"); return redirect(url_for("index"))
    finally:
        if path.exists(): path.unlink()

@app.route("/api/check", methods=["POST"])
def api_check():
    from checker import grade
    file = request.files.get("file")
    if not file or not _ok(file.filename):
        return jsonify({"success":False,"error":"invalid file"}), 400
    path = UPLOAD_DIR / secure_filename(file.filename)
    file.save(path)
    try:    return jsonify(grade(str(path)))
    finally: path.unlink(missing_ok=True)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
