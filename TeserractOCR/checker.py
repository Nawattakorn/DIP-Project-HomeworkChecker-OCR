"""
checker.py - Load answer key,Correction, run OCR, return grading result.
"""

import json
import re
from pathlib import Path
from ocr import extract_answers

ANSWER_KEY_PATH = Path(__file__).parent / "answer_key.json"

def _normalise(text: str) -> str:
    """ลบช่องว่างและทำเป็นตัวพิมพ์ใหญ่ทั้งหมด เพื่อใช้เปรียบเทียบ"""
    return re.sub(r"\s+", "", str(text).strip().upper())

def _postprocess(raw: str, expected: str) -> str:
    """
    ดึงคำตอบสุดท้ายจากข้อความดิบที่ OCR อ่านได้ 
    พร้อมระบบเดาบริบทจาก "เฉลย" ว่าควรจะเป็นตัวเลขหรือคำศัพท์
    """
    expected_norm = _normalise(expected)
    
    # ถ้าเฉลยเป็น "ตัวเลขล้วน" ให้ใช้ระบบแก้คำผิด (OCR Confusions)
    if expected_norm.isdigit():
        # ดิกชันนารีแปลงตัวอักษรที่มักจะอ่านพลาด ให้กลับเป็นตัวเลข
        corrections = {
            'G': '9', 'g': '9', 
            'S': '5', 's': '5', 
            'O': '0', 'o': '0', 'Q': '0',
            'L': '1', 'l': '1', 'I': '1', 'i': '1', 
            'Z': '2', 'z': '2', 
            'B': '8',
            'A': '4',
        }
        
        # แทนที่ตัวอักษรที่ผิดพลาดให้เป็นตัวเลข
        fixed_raw = "".join([corrections.get(c, c) for c in raw])
        
        # ดึงมาเฉพาะตัวเลขจริงๆ
        nums = re.findall(r"\d+", fixed_raw)
        return nums[-1] if nums else ""
    
    # ถ้าเฉลยเป็น "คำศัพท์" ก็ส่งคืนข้อความที่อ่านได้ตามปกติ
    return _normalise(raw)

def grade(image_path: str, key_path: str = None, provided_key: list = None) -> dict:
    """
    ตรวจการบ้าน โดยใช้เฉลยจากไฟล์ หรือจากที่ user กรอกมาโดยตรง
    """
    if provided_key:
        # รับเฉลยจากหน้าเว็บ ไม่ต้องระบุ type แล้ว เพราะระบบจะเดาเอง
        questions = [{"id": i+1, "answer": str(ans)} 
                     for i, ans in enumerate(provided_key)]
    else:
        key_path = key_path or ANSWER_KEY_PATH
        with open(key_path, encoding="utf-8") as f:
            key = json.load(f)
        questions = key.get("questions", [])

    try:
        raw_lines = extract_answers(image_path)
    except Exception as e:
        return {"success": False, "error": str(e), "score": 0, "results": []}

    # จับคู่คำตอบที่อ่านได้กับเฉลย
    raw_lines = (raw_lines + [""] * len(questions))[: len(questions)]
    results = []
    correct_count = 0

    for i, q in enumerate(questions):
        expected = str(q.get("answer", ""))
        expected_norm = _normalise(expected)
        
        # ส่ง expected ไปให้ _postprocess ช่วยตัดสินใจ
        got = _postprocess(raw_lines[i], expected)
        
        ok = (got == expected_norm)
        if ok: correct_count += 1

        results.append({
            "id": q.get("id", i + 1),
            "expected": expected_norm,
            "got": got,
            "correct": ok
        })

    score = round(correct_count / len(questions) * 100, 1) if questions else 0
    return {
        "success": True,
        "score": score,
        "correct": correct_count,
        "total": len(questions),
        "results": results,
        "extracted_raw": raw_lines,
    }