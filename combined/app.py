"""app.py - Homework Checker (Combined)"""
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
    import re
    
    file = request.files.get("file")
    answers_raw = request.form.get("answers_raw", "")
    engine = request.form.get("engine", "corr2")
    
    if not file or not file.filename:
        flash("กรุณาเลือกไฟล์","error"); return redirect(url_for("index"))
    if not _ok(file.filename):
        flash("รองรับ PNG/JPG/JPEG/BMP","error"); return redirect(url_for("index"))
    
    user_key = [a.strip() for a in re.split(r'[\n,]+', answers_raw.strip()) if a.strip()]

    path = UPLOAD_DIR / secure_filename(file.filename)
    file.save(path)
    
    try:
        if engine == "compare":
            # รัน 3 engines พร้อมกัน
            from checker_corr2    import grade as grade_corr2
            from checker_teserract import grade as grade_tess
            from checker_trocr    import grade as grade_trocr
            from ocr_corr2        import extract_answers_debug as debug_corr2
            from ocr_teserract    import extract_answers_debug as debug_tess
            from ocr_trocr        import extract_answers_debug as debug_trocr

            results_all = {
                "corr2":     grade_corr2(str(path),   provided_key=user_key),
                "teserract": grade_tess(str(path),    provided_key=user_key),
                "trocr":     grade_trocr(str(path),   provided_key=user_key),
            }
            steps_all = {
                "corr2":     debug_corr2(str(path))[1],
                "teserract": debug_tess(str(path))[1],
                "trocr":     debug_trocr(str(path))[1],
            }
            return render_template("compare.html",
                                   results_all=results_all,
                                   steps_all=steps_all,
                                   user_key=user_key)

        # Single Engine
        if engine == "teserract":
            from checker_teserract import grade
            from ocr_teserract import extract_answers_debug
        elif engine == "trocr":
            from checker_trocr import grade
            from ocr_trocr import extract_answers_debug
        else: # default to corr2
            from checker_corr2 import grade
            from ocr_corr2 import extract_answers_debug

        result = grade(str(path), provided_key=user_key)
        _, steps = extract_answers_debug(str(path))
        return render_template("result.html", result=result, steps=steps, engine=engine)
    except Exception as e:
        flash(f"Error: {e}","error"); return redirect(url_for("index"))
    finally:
        try:
            if path.exists(): 
                path.unlink()
        except PermissionError:
            pass

@app.route("/api/check", methods=["POST"])
def api_check():
    engine = request.form.get("engine", "corr2")
    
    if engine == "teserract":
        from checker_teserract import grade
    elif engine == "trocr":
        from checker_trocr import grade
    else: 
        from checker_corr2 import grade

    file = request.files.get("file")
    if not file or not _ok(file.filename):
        return jsonify({"success":False,"error":"invalid file"}), 400
    path = UPLOAD_DIR / secure_filename(file.filename)
    file.save(path)
    try:    
        return jsonify(grade(str(path)))
    finally: 
        try:
            path.unlink(missing_ok=True)
        except:
            pass

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
