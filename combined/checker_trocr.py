"""
checker.py - Grading Logic 
"""
import json
import re
from pathlib import Path
from ocr_trocr import extract_answers

def _normalise(text: str) -> str:
    """ลบเว้นวรรคและทำเป็นตัวใหญ่ทั้งหมดเพื่อเทียบเฉลย"""
    return re.sub(r"\s+", "", str(text).strip().upper())

def _postprocess(raw: str, expected: str) -> str:
    """ทำความสะอาดคำตอบที่ TrOCR อ่านมาได้ และพยายาม extract เฉพาะส่วนที่เกี่ยวข้อง"""
    expected_norm = _normalise(expected)

    # 1. ลบ trailing noise ที่ TrOCR มักเพิ่มมา เช่น " ." หรือ "." ท้ายคำ
    raw_clean = raw.strip().rstrip('. ')

    raw_norm = _normalise(raw_clean)

    # 2. ถ้าเฉลยเป็นตัวเลขล้วน → ดึงตัวเลขออก
    if expected_norm.isdigit():
        nums = re.findall(r"\d+", raw_norm)
        return nums[-1] if nums else raw_norm

    # 3. ลบสัญลักษณ์พิเศษทิ้ง เหลือแต่ A-Z 0-9
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_norm)

    # 4. ถ้าเฉลยซ่อนอยู่ใน cleaned (เช่น EAST ใน EXEAST, RIDES ใน SHELRIDES)
    #    ให้ดึงเฉพาะส่วนที่ตรงออกมาแสดง แทนที่จะแสดงทั้งก้อน
    if expected_norm and expected_norm in cleaned and cleaned != expected_norm:
        idx = cleaned.find(expected_norm)
        return cleaned[idx: idx + len(expected_norm)]

    return cleaned

def grade(image_path: str, key_path: str = None, provided_key: list = None) -> dict:
    if provided_key:
        questions = [{"id": i+1, "answer": str(ans)} for i, ans in enumerate(provided_key)]
    else:
        questions = []

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
