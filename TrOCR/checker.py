"""
checker.py - Grading Logic (เวอร์ชัน Google Cloud Vision)
"""
import json
import re
from pathlib import Path
from ocr import extract_answers

ANSWER_KEY_PATH = Path(__file__).parent / "answer_key.json"

def _normalise(text: str) -> str:
    """ลบเว้นวรรคและทำเป็นตัวใหญ่ทั้งหมดเพื่อเทียบเฉลย"""
    return re.sub(r"\s+", "", str(text).strip().upper())

def _postprocess(raw: str, expected: str) -> str:
    """ทำความสะอาดคำตอบที่ Google อ่านมาได้"""
    expected_norm = _normalise(expected)
    raw_norm = _normalise(raw)
    
    # ถ้าเฉลยข้อนี้เป็นตัวเลขล้วน
    if expected_norm.isdigit():
        nums = re.findall(r"\d+", raw_norm)
        return nums[-1] if nums else raw_norm
    
    # ถ้าเฉลยเป็นภาษาอังกฤษ (ลบสัญลักษณ์พิเศษทิ้งให้เหลือแต่ตัวอักษร)
    return re.sub(r'[^A-Z0-9]', '', raw_norm)

def grade(image_path: str, key_path: str = None, provided_key: list = None) -> dict:
    if provided_key:
        questions = [{"id": i+1, "answer": str(ans)} for i, ans in enumerate(provided_key)]
    else:
        key_path = key_path or ANSWER_KEY_PATH
        with open(key_path, encoding="utf-8") as f:
            key = json.load(f)
        questions = key.get("questions", [])

    try:
        raw_lines = extract_answers(image_path)
    except Exception as e:
        return {"success": False, "error": str(e), "score": 0, "results": []}

    raw_lines = (raw_lines + [""] * len(questions))[: len(questions)]
    results = []
    correct_count = 0

    for i, q in enumerate(questions):
        expected = str(q.get("answer", ""))
        expected_norm = _normalise(expected)
        
        got = _postprocess(raw_lines[i], expected)
        
        # ตรวจใจกว้าง: ถ้ามีเฉลยซ่อนอยู่ในสิ่งที่อ่านได้ ถือว่าถูก
        ok = (expected_norm == got) or (expected_norm in got if expected_norm else False)
        
        if ok: correct_count += 1

        results.append({
            "id": q.get("id", i + 1),
            "expected": expected_norm,
            "got": got,
            "correct": ok
        })

    score = round(correct_count / len(questions) * 100, 1) if questions else 0
    return {
        "success": True, "score": score,
        "correct": correct_count, "total": len(questions),
        "results": results, "extracted_raw": raw_lines,
    }